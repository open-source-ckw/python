# ai-agent/py/src/ask.py
"""
Vector search over knowledge.db with optional LLM or offline local summarization.
Supports:
--mode llm (OpenAI chat with your local DB context)
--mode local --local-style extractive (TF‑IDF + MMR Offline | --local-style extractive: ignores --abs-model and all --abs-* knobs. | Picks the most relevant sentences from retrieved chunks (TF‑IDF + MMR). No neural generation. Fast, stable, and grounded in exact repo text. Ignores all abstractive flags like --abs-model, --abs-*. Requires scikit‑learn.)
--mode local --local-style abstractive (PyTorch+Transformers on CPU, offline | --local-style abstractive: requires a model (HF ID or local dir). Uses --abs-* knobs. | Abstractive: Uses a local seq2seq model (your --abs-model) to write a concise answer from selected notes/context. Can be more readable but may get terse/generic on small models. Slower; respects --abs-model, --abs-max-input-toks, --abs-max-new, --abs-beams.)
--mode local --local-style basic (raw matches | --local-style basic: prints raw chunks; ignores --abs-*.)

Usage examples:
  # Local raw db (offline data direct from db)
  npm run ai:ask -- --mode local --local-style basic "how to manage env variables?"

  # LLM mode (default): context → OpenAI Chat
  npm run ai:ask -- "how to manage env variables?"
  or
  npm run ai:ask -- --mode llm "how to manage env variables?"

  # Local extractive (offline, no OpenAI Chat)
  npm run ai:ask -- --mode local --local-style extractive "how to manage env variables?"

  # Local abstractive (offline CPU; requires torch + transformers - this uses google/flan-t5-small under the hood but shows error as it try to use from internet)
  npm run ai:ask -- --mode local --local-style abstractive "how to manage env variables?"

  # swap at runtime t5-small
  npm run ai:ask -- --mode local --local-style abstractive --abs-model /Users/core/ai/models/google-t5__t5-small "how to manage env variables?"
  
  # light weight model download google/flan-t5-small from huggingface.co
  npm run ai:ask -- --mode local --local-style abstractive --abs-model /Users/core/ai/models/google__flan-t5-small "how to manage env variables?"
    
  # or (better summarizer, a bit heavier) download sshleifer/distilbart-cnn-12-6 from huggingface.co
  npm run ai:ask -- --mode local --local-style abstractive --abs-model /Users/core/ai/models/sshleifer__distilbart-cnn-12-6 "how to manage env variables?"

  # Dump retrieved chunks JSON
  npm run ai:ask -- --mode local --json "playwright backspace timing"

  

"""

from datetime import datetime, UTC, date
from pathlib import Path
import os, sys, json, sqlite3, argparse, re

import sqlite_vec
from sqlite_vec import serialize_float32

# add this import near your other imports
import numpy as np
import re

_CITE_RE = re.compile(r"\[(\d+|\d+(?:,\s*\d+)+)\]")   # [1], [1, 2]
_MULTI_CITE_RE = re.compile(r"(?:\[\d+\]\s*){2,}")     # [1][2][3] spam
_WS_RE = re.compile(r"\s+")

def strip_citations(text: str) -> str:
    if not text: return text
    t = _MULTI_CITE_RE.sub(" ", text)
    t = _CITE_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t

def ensure_min_length(s: str, min_chars=60) -> bool:
    return bool(s) and len(s.strip()) >= min_chars

# --- Optional deps for local modes ---
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as csim
    SKLEARN_OK = True
except Exception:
    SKLEARN_OK = False

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    HF_OK = True
except Exception:
    HF_OK = False

# --- Project config (paths +, ideally, OpenAI creds) ---
from conf import ROOT, DB_PATH, LOCK_PATH, SESSIONS_DIR, INBOX_DIR, OUTBOX_DIR, PROPOSALS_FILE  # noqa: F401

# OpenAI config (allow env fallback if not defined in config.py)
try:
    from conf import OPENAI_API_KEY, OPENAI_EMBED_MODEL, OPENAI_CHAT_MODEL
except Exception:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")
    OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

# OpenAI client (only used in LLM mode and for query embeddings)
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Derived paths ---
DB = str(DB_PATH)
SESS_DIR = str(SESSIONS_DIR)
INBOX = str(Path(INBOX_DIR) / PROPOSALS_FILE)

# ----------------- time helpers -----------------
def parse_ts(ts: str):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

def recency_score(ts: str, now=None, half_life_days=14):
    """0..1 where 1 = just now. Exponential decay with 14-day half-life."""
    if not ts:
        return 0.0
    now = now or datetime.now(UTC)
    dt = parse_ts(ts)
    if not dt:
        return 0.0
    age_days = (now - dt).total_seconds() / 86400.0
    return pow(0.5, age_days / half_life_days)

# ----------------- embeddings -----------------
def embed(text: str):
    # Note: even in local modes we still need a query embedding unless you replace retrieval too.
    return client.embeddings.create(model=OPENAI_EMBED_MODEL, input=text).data[0].embedding

# ----------------- vector search (HEAD only) -----------------
def knn(query_emb, k=6, pool=50, w_time=0.35):
    """
    Returns top-k chunks with blended score:
      score = (1 - w_time) * vector_similarity + w_time * recency_boost
    Searches only the latest (HEAD) revisions by joining vec -> chunks_head.
    """
    pool = int(pool); topk = int(k)

    db = sqlite3.connect(DB)
    db.enable_load_extension(True)
    sqlite_vec.load(db)  # provides vec0
    db.enable_load_extension(False)
    db.execute("PRAGMA busy_timeout=5000")

    qbytes = serialize_float32(query_emb)

    sql = f"""
        SELECT
          c.id       AS chunk_id,
          v.distance AS distance,
          c.source, c.kind, c.key, c.seq,
          c.content, c.updated_at
        FROM vec_chunks v
        JOIN chunks_head c ON c.id = v.chunk_id
        WHERE v.embedding MATCH ?
          AND v.k = {pool}
        ORDER BY v.distance ASC
        LIMIT {max(pool, topk)}
    """
    rows = db.execute(sql, (qbytes,)).fetchall()

    # Normalize distances to similarities, blend with recency
    dists = [r[1] for r in rows] or [1.0]
    dmin, dmax = min(dists), max(dists)

    def sim_from_dist(d):
        if dmax == dmin:
            return 1.0
        return 1.0 - (d - dmin) / (dmax - dmin)

    now = datetime.now(UTC)
    scored = []
    for (chunk_id, dist, source, kind, key, seq, content, updated_at) in rows:
        s_sim = sim_from_dist(dist)
        s_time = recency_score(updated_at, now=now)
        score = (1 - w_time) * s_sim + w_time * s_time
        scored.append({
            "chunk_id": chunk_id,
            "dist": dist,
            "sim": s_sim,
            "time": s_time,
            "score": score,
            "source": source,
            "kind": kind,
            "key": key,
            "seq": seq,
            "updated_at": updated_at,
            "content": content,
        })

    scored.sort(key=lambda c: c["score"], reverse=True)
    return scored[:topk]

# ----------------- LLM answer -----------------
# near your imports
def _supports_temperature(model_name: str) -> bool:
    """
    Returns False for 'reasoning' style models that don't accept custom temperature.
    Adjust the list as needed if you use other restricted models.
    """
    m = (model_name or "").lower()
    restricted_fragments = ("o1", "o3", "gpt-5")  # expand if needed
    return not any(frag in m for frag in restricted_fragments)

def llm_answer(query: str, ctx: list):
    blocks = []
    for i, c in enumerate(ctx, 1):
        blocks.append(f"[{i}] ({c['source']}#{c['seq']}, score={c['score']:.4f})\n{c['content']}")
    context_text = "\n\n---\n\n".join(blocks) if blocks else "(no context)"

    system = (
        "You are a precise project assistant. Use ONLY the given context to answer. "
        "Cite snippets with [1], [2], etc. If the context is insufficient, say exactly what's missing."
    )
    user = f"Question: {query}\n\nContext:\n{context_text}\n\nAnswer concisely. Include code if useful."

    kwargs = {
        "model": OPENAI_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if _supports_temperature(OPENAI_CHAT_MODEL):
        kwargs["temperature"] = 0.2

    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content.strip()


# ----------------- Local (no-LLM) helpers -----------------
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
def sent_tokenize(text: str):
    text = (text or "").strip()
    if not text:
        return []
    parts = _SENT_SPLIT_RE.split(text)
    return [" ".join(p.split()) for p in parts if p.strip()]

def truncate(s: str, n=600):
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + " …[truncated]"

# ---- Helpers to improve abstractive answers ----
def model_family(name: str) -> str:
    n = (name or "").lower()
    if "bart" in n or "distilbart" in n:
        return "bart"
    if "t5" in n or "flan" in n:
        return "t5"
    return "seq2seq"

GENERIC_PHRASES = (
    "described in this repo",
    "documented in the repo",
    "the manual process is documented",
    "the exact manual process",
    "this repository",
)

def looks_generic(s: str) -> bool:
    if not ensure_min_length(s, 80):
        return True
    t = (s or "").strip().lower()
    bad_frags = (
        "i don't have", "cannot access", "as an ai", "i am an ai",
        "insufficient context", "not enough context", "cannot determine",
        "depends on", "in general", "best practices include",
    )
    return any(p in t for p in GENERIC_PHRASES) or any(b in t for b in bad_frags)

def build_basic_context(ctx: list, top_n=3, per_chunk_chars=1000) -> str:
    """Compact, readable context from top chunks, preserving paths and content."""
    blocks = []
    for i, c in enumerate(ctx[:top_n], 1):
        head = f"[{i}] {c['source']}#{c['seq']} (kind={c['kind']}, score={c['score']:.3f})"
        body = truncate(strip_citations(c.get("content", "")), per_chunk_chars)
        blocks.append(f"{head}\n{body}")
    return "\n\n---\n\n".join(blocks)

def basic_local_answer(query: str, ctx: list):
    if not ctx:
        return "No local matches found."
    lines = ["Top matches (no LLM used):", ""]
    for i, c in enumerate(ctx, 1):
        head = f"[{i}] {c['source']}#{c['seq']}  kind={c['kind']}  score={c['score']:.3f}  sim={c['sim']:.3f}  time={c['time']:.3f}"
        ts   = f"updated_at={c['updated_at']}"
        body = truncate(c["content"], 900)
        lines.append(head); lines.append(ts); lines.append(body); lines.append("")
    return "\n".join(lines)

# ---- Candidate sentence selection (TF-IDF + MMR) ----
def select_salient_sentences(query: str, ctx: list, max_sents=18, max_per_chunk=7, mmr_lambda=0.68):
    # Build candidates: (sentence, tag, weight)
    cands = []
    for c in ctx:
        tag = f"{c['source']}#{c['seq']}"
        if c["kind"] in ("memory_item","instruction_item","style_note"):
            sents = [c["content"].strip()]
        else:
            sents = sent_tokenize(c["content"])
        kept = 0
        for s in sents:
            s_clean = strip_citations(s)
            L = len(s_clean)
            # prefer medium sentences; skip very short/noisy
            if 36 <= L <= 360:
                # weight: retrieval score with a stronger recency boost and config bias
                cfg_bias = 1.15 if any(k in (c.get("source","")+s_clean).lower() for k in ("config", ".env", "dotenv", "schema", "validation", "configmodule")) else 1.0
                w = c["score"] * (1.0 + 0.28 * c["time"]) * cfg_bias
                cands.append((s_clean, tag, w))
                kept += 1
                if kept >= max_per_chunk: break

    if not cands:
        return [], []

    # quick de-dup (case-insensitive)
    seen = set(); dedup = []
    for s, tag, w in cands:
        k = s.lower()
        if k in seen: continue
        seen.add(k); dedup.append((s, tag, w))

    # If sklearn missing, pick top by weight
    if not SKLEARN_OK:
        dedup.sort(key=lambda t: t[2], reverse=True)
        chosen = dedup[:max_sents]
        tags = [t[1] for t in chosen]
        return [t[0] for t in chosen], tags

    # TF-IDF vectors for query + sentences
    texts = [query] + [s for (s,_tag,_w) in dedup]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_df=0.9)
    X = vec.fit_transform(texts)
    q = X[0:1]; S = X[1:]
    sim_q = csim(S, q).ravel()                  # numpy array
    weights = np.asarray([w for (_s,_t,w) in dedup], dtype=float)
    # normalize weights
    if weights.max() > weights.min():
        norm_w = (weights - weights.min()) / (weights.max() - weights.min())
    else:
        norm_w = np.zeros_like(weights)
    base = 0.7 * sim_q + 0.3 * norm_w

    # MMR diversity
    n = len(dedup); k = max(1, min(max_sents, n))
    chosen_idx = []
    S2S = csim(S, S)
    while len(chosen_idx) < k:
        best_i, best_val = -1, -1e9
        for i in range(n):
            if i in chosen_idx: continue
            penalty = max((S2S[i][j] for j in chosen_idx), default=0.0)
            val = mmr_lambda * base[i] - (1 - mmr_lambda) * penalty
            if val > best_val:
                best_val, best_i = val, i
        if best_i < 0: break
        chosen_idx.append(best_i)

    chosen = [dedup[i] for i in chosen_idx]
    tags = [t[1] for t in chosen]
    return [t[0] for t in chosen], tags


# ---- Extractive summary (offline) ----
def extractive_local_answer(query: str, ctx: list, max_sents=6, mmr_lambda=0.7):
    if not ctx:
        return "No local matches found."

    # Prefer sklearn route; otherwise fallback to basic listing
    if not SKLEARN_OK:
        return basic_local_answer(query, ctx)

    sents, tags = select_salient_sentences(query, ctx, max_sents=max_sents, mmr_lambda=mmr_lambda)
    if not sents:
        return basic_local_answer(query, ctx)

    # Light post-process: dedupe again and keep order
    out_sents, seen = [], set()
    for s in sents:
        k = s.lower()
        if k in seen: continue
        seen.add(k); out_sents.append(s)

    bullets = [f"- {s}" for s in out_sents]
    uniq_tags = []
    for t in tags:
        if t not in uniq_tags: uniq_tags.append(t)

    return (
        "Local summary (extractive, no model):\n\n"
        + "\n".join(bullets)
        + "\n\nReferences:\n"
        + "\n".join(f"  • {t}" for t in uniq_tags)
    )


# ---- Abstractive summarization (PyTorch + Transformers, CPU) ----
_ABS_MODEL = None
_ABS_TOK = None

def load_abstractive(model_name: str):
    global _ABS_MODEL, _ABS_TOK
    if not HF_OK:
        return False, "Transformers/PyTorch not installed"
    if _ABS_MODEL is None or _ABS_TOK is None:
        _ABS_TOK = AutoTokenizer.from_pretrained(model_name)
        _ABS_MODEL = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        _ABS_MODEL.eval()
    return True, ""

def abstractive_local_answer(
    query: str, ctx: list,
    model_name="google/flan-t5-small",
    max_sents=12, max_input_tokens=640, max_new_tokens=160, num_beams=4
):
    if not ctx:
        return "No local matches found."

    ok, msg = load_abstractive(model_name)
    if not ok:
        return extractive_local_answer(query, ctx, max_sents=max_sents)

    fam = model_family(model_name)

    # 1) Select salient sentences (short, high-signal)
    sents, tags = select_salient_sentences(query, ctx, max_sents=max_sents)
    if not sents:
        return basic_local_answer(query, ctx)

    tok = _ABS_TOK
    # Clamp to tokenizer/model limit to avoid warnings like "1335 > 512"
    tok_limit = getattr(tok, "model_max_length", None) or 512
    try:
        tok_limit = int(tok_limit)
    except Exception:
        tok_limit = 512
    budget = min(max_input_tokens, tok_limit)

    def pack_text(lines):
        packed, total = [], 0
        for s in lines:
            s2 = strip_citations(s)
            ids = tok.encode(s2, add_special_tokens=False, truncation=True, max_length=budget)
            if total + len(ids) > budget:
                break
            packed.append(s2)
            total += len(ids)
        return packed

    # 2) Pack notes and build a richer basic context
    notes_lines = pack_text(sents)
    notes = ("\n- " + "\n- ".join(notes_lines)) if notes_lines else ""

    rich_ctx = build_basic_context(ctx, top_n=3, per_chunk_chars=1000)
    # Ensure rich context stays within token budget if used
    rc_ids = tok.encode(rich_ctx, add_special_tokens=False, truncation=True, max_length=budget)
    if len(rc_ids) > budget:
        rich_ctx = tok.decode(rc_ids[:budget], skip_special_tokens=True)

    # 3) Model-aware prompts
    if fam == "t5":
        prompt_notes = (
            "summarize: You are writing a precise, project-specific answer.\n"
            f"Question: {query}\n"
            f"Notes:{notes}\n\n"
            "Write a short, actionable answer with clear steps. Include file paths and code when present. "
            "Use only the provided notes; if something is missing, state exactly what's missing."
        )
        prompt_ctx = (
            "summarize: Use ONLY the context to answer precisely.\n"
            f"Question: {query}\n\n"
            f"Context:\n{rich_ctx}\n\n"
            "Write concise, concrete steps. Include repo paths and code when present. "
            "If info is missing, say exactly what's missing."
        )
    else:  # bart/distilbart and other seq2seq
        prompt_notes = (
            f"You are writing an exact, project-aware answer.\n"
            f"Question: {query}\n\n"
            f"Key facts from the repo (deduplicated):\n{notes}\n\n"
            "Instructions: Provide a practical, step-by-step guide for this project.\n"
            "- Mention exact files and paths (e.g., .env, ConfigModule schema).\n"
            "- Show minimal code examples fenced with ``` for env loading/validation.\n"
            "- Prefer precise patterns over generalities; do not add fluff.\n"
            "- If something is missing, state exactly what's missing.\n"
        )
        prompt_ctx = (
            f"Project question: {query}\n\n"
            f"Relevant context:\n{rich_ctx}\n\n"
            "Write a compact, actionable answer for THIS repo.\n"
            "- Name files/paths exactly as shown.\n"
            "- Include at least one fenced code block with env/config usage.\n"
            "- Avoid generic advice; only use the provided context.\n"
        )

    def generate(text):
        inpt = tok(text, return_tensors="pt", truncation=True, max_length=budget)
        with torch.no_grad():
            out = _ABS_MODEL.generate(
                **inpt,
                max_new_tokens=max_new_tokens,
                num_beams=max(4, num_beams),
                no_repeat_ngram_size=4,
                repetition_penalty=1.12,
                early_stopping=True,
            )
        return strip_citations(tok.decode(out[0], skip_special_tokens=True).strip())

    # Helper to detect whether generated text includes concrete artifacts
    def _has_concrete_bits(t: str) -> bool:
        t2 = (t or "").lower()
        has_path = any(p in t2 for p in (".env", "config", "schema", "validation", "ai-agent/", "src/", "/"))
        has_code = "```" in (t or "")
        return has_path and has_code

    # 4) Try prompts (order depends on model family) with a small retry loop
    order = ("ctx_first" if fam == "bart" else "notes_first")
    text = ""
    attempts = 0
    max_attempts = 3
    last_try_sources = []
    while attempts < max_attempts:
        attempts += 1
        if order == "ctx_first":
            text = generate(prompt_ctx)
            last_try_sources.append("ctx")
            if looks_generic(text):
                text2 = generate(prompt_notes)
                last_try_sources.append("notes")
                if ensure_min_length(text2, 80) and not looks_generic(text2):
                    text = text2
        else:
            text = generate(prompt_notes)
            last_try_sources.append("notes")
            if looks_generic(text):
                text2 = generate(prompt_ctx)
                last_try_sources.append("ctx")
                if ensure_min_length(text2, 80) and not looks_generic(text2):
                    text = text2

        # Enforce presence of code/path; if missing, retry with stricter instruction appended
        if _has_concrete_bits(text):
            break
        if attempts < max_attempts:
            # tighten the instruction and retry
            extra = ("\n\nRETRY INSTRUCTIONS: The previous answer lacked explicit file paths or code examples. "
                     "Now produce: (1) a one-line summary, (2) numbered actionable steps, "
                     "(3) at least one fenced code block or explicit file/key.")
            prompt_ctx += extra
            prompt_notes += extra
            # also toggle order to try the other prompt first next iteration
            order = "notes_first" if order == "ctx_first" else "ctx_first"

    # 5) Guardrails: ensure we have concrete bits (paths + code). If weak, hybridize.
    def _has_concrete_bits(t: str) -> bool:
        t2 = (t or "").lower()
        has_path = any(p in t2 for p in (".env", "config", "schema", "validation", "ai-agent/", "src/", "/"))
        has_code = "```" in (t or "")
        return has_path and has_code

    # 6) If still weak, produce a hybrid (abstractive + extractive bullets)
    if looks_generic(text) or not _has_concrete_bits(text):
        # reuse the previously selected salient sentences; expand a bit if needed
        hyb_sents, _ = select_salient_sentences(query, ctx, max_sents=min(8, max_sents + 2))
        out_sents, seen = [], set()
        for s in hyb_sents:
            k = (s or "").strip().lower()
            if not k or k in seen:
                continue
            seen.add(k)
            out_sents.append(s)

        bullets = "\n".join(f"- {s}" for s in out_sents)
        header = "Local summary (hybrid: abstractive + key details):"
        if not bullets:
            return extractive_local_answer(query, ctx, max_sents=min(8, max_sents + 2))
        # Rewrite into a coherent flow: intro, ordered steps, notes.
        steps = []
        for b in out_sents:
            # light normalization: convert imperatives, remove trailing punctuation
            t = b.strip()
            t = re.sub(r"^[A-Z].{0,12}:\\s*", "", t)  # drop short leading labels like "Env:" or "Config:"
            t = t.rstrip(".;")
            steps.append(t)
        numbered = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        flow = (
            f"{header}\n\n"
            "Do the following in order:\n\n"
            f"{numbered}\n\n"
            "Key snippets from context:\n"
            f"{bullets}"
        )
        return flow

    # 7) references to the used chunks
    uniq_tags = []
    for t in tags:
        if t not in uniq_tags:
            uniq_tags.append(t)

    # Light post-edit to improve flow: merge short lines, ensure continuity.
    def _tidy(paragraph: str) -> str:
        parts = [ln.strip() for ln in paragraph.splitlines()]
        out, buf = [], []
        for ln in parts:
            if not ln:
                if buf:
                    out.append(" ".join(buf)); buf = []
                out.append("")
            elif len(ln) < 40 and not ln.endswith(":"):
                buf.append(ln)
            else:
                if buf:
                    out.append(" ".join(buf)); buf = []
                out.append(ln)
        if buf:
            out.append(" ".join(buf))
        # de-duplicate consecutive lines
        dedup = []
        for ln in out:
            if not dedup or dedup[-1] != ln:
                dedup.append(ln)
        return "\n".join(dedup)

    text = _tidy(text)
    header = "Local summary (abstractive, offline CPU):"
    return f"{header}\n\n{text}\n\nReferences:\n" + "\n".join(f"  • {t}" for t in uniq_tags)


# ----------------- session logging -----------------
def append_session(question: str, answer: str, agent="rag-search"):
    os.makedirs(SESS_DIR, exist_ok=True)
    today = date.today().isoformat()
    fpath = Path(SESS_DIR) / f"{today}.jsonl"
    turn_id = f"{agent}-{datetime.now(UTC).strftime('%H%M%S%f')}"

    rec = {
        "ts": datetime.now(UTC).isoformat(),
        "turn_id": turn_id,
        "agent": agent,
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
    }
    with open(fpath, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return turn_id

# ----------------- proposals (optional; off by default) -----------------
def maybe_propose_facts(turn_id: str, answer_text: str, module: str = ""):
    """
    Extract up to 2 bullets from the LLM/Local answer and write a memory proposal.
    Your watcher expects 'module' for memory proposals; if missing, skip.
    """
    module = (module or "").strip().lower()
    if not module:
        return

    bullets = [ln[1:].strip() for ln in answer_text.splitlines() if ln.strip().startswith("-")]
    bullets = [b for b in bullets if 8 <= len(b) <= 240][:2]
    if not bullets:
        return

    os.makedirs(INBOX_DIR, exist_ok=True)
    prop = {
        "ts": datetime.now(UTC).isoformat() + "Z",
        "proposal_id": f"p-{turn_id}",
        "type": "memory",
        "target": "memory.yaml",
        "bullets": bullets,
        "rationale": "Derived from search answer; candidate durable facts",
        "source_turn_id": turn_id,
        "agent": "rag-search",
        "module": module,
    }
    with open(INBOX, "a", encoding="utf-8") as f:
        f.write(json.dumps(prop, ensure_ascii=False) + "\n")

# ----------------- CLI -----------------
def main():
    ap = argparse.ArgumentParser(description="Vector search over knowledge.db with optional LLM or offline local summarization.")
    ap.add_argument("--mode", choices=["llm","local"], default=os.environ.get("AI_SEARCH_MODE","llm"),
                    help="llm = OpenAI chat; local = no OpenAI chat")
    ap.add_argument("--local-style", choices=["basic","extractive","abstractive"],
                    default=os.environ.get("AI_LOCAL_STYLE","extractive"),
                    help="Local rendering style (no OpenAI).")
    ap.add_argument("--k", type=int, default=6, help="top-k results to return (default 6)")
    ap.add_argument("--pool", type=int, default=50, help="initial candidates from vec (default 50)")
    ap.add_argument("--w-time", type=float, default=0.35, help="blend weight for recency (0..1, default 0.35)")
    ap.add_argument("--json", action="store_true", help="also print JSON of retrieved chunks")
    ap.add_argument("--no-session", action="store_true", help="do not append this turn to sessions")
    ap.add_argument("--propose", action="store_true", default=(os.environ.get("AI_SEARCH_PROPOSE") == "1"),
                    help="after answer, write a memory proposal (requires --module)")
    ap.add_argument("--module", default=os.environ.get("AI_AGENT_MODULE","").strip(),
                    help="module bucket for proposals (e.g., 'infra.env', 'playwright')")
    # Abstractive knobs
    ap.add_argument("--abs-model", default=os.environ.get("AI_ABS_MODEL","google/flan-t5-small"),
                    help="Small CPU-friendly seq2seq model (e.g., google/flan-t5-small, t5-small)")
    ap.add_argument("--abs-max-sents", type=int, default=int(os.environ.get("AI_ABS_MAX_SENTS","20")))
    ap.add_argument("--abs-max-input-toks", type=int, default=int(os.environ.get("AI_ABS_MAX_INPUT","480")))
    ap.add_argument("--abs-max-new", type=int, default=int(os.environ.get("AI_ABS_MAX_NEW","128")))
    ap.add_argument("--abs-beams", type=int, default=int(os.environ.get("AI_ABS_BEAMS","4")))
    ap.add_argument("question", nargs="*", help="Your query")
    args = ap.parse_args()

    query = " ".join(args.question).strip() or "How do we validate DTOs in this project?"

    # 1) retrieve
    q_emb = embed(query)
    ctx = knn(q_emb, k=args.k, pool=args.pool, w_time=args.w_time)

    # 2) answer
    if args.mode == "local":
        if args.local_style == "abstractive":
            ans = abstractive_local_answer(
                query, ctx,
                model_name=args.abs_model,
                max_sents=args.abs_max_sents,
                max_input_tokens=args.abs_max_input_toks,
                max_new_tokens=args.abs_max_new,
                num_beams=args.abs_beams,
            )
            agent_name = "rag-search-local-abs"
        elif args.local_style == "extractive":
            ans = extractive_local_answer(query, ctx, max_sents=6)
            agent_name = "rag-search-local"
        else:
            ans = basic_local_answer(query, ctx)
            agent_name = "rag-search-local"
    else:
        ans = llm_answer(query, ctx)
        agent_name = "rag-search"

    # 3) output
    print("\n=== Answer ===\n")
    print(ans)

    if args.json:
        print("\n--- JSON (retrieved chunks) ---")
        print(json.dumps(ctx, ensure_ascii=False, indent=2))

    # 4) session + optional proposal
    if not args.no_session and os.environ.get("AI_SEARCH_LOG","1") != "0":
        turn_id = append_session(query, ans, agent=agent_name)
        if args.propose:
            maybe_propose_facts(turn_id, ans, module=args.module)

if __name__ == "__main__":
    main()
