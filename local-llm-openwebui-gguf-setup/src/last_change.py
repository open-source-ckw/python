#!/usr/bin/env python3
# How to run this file with various options:
# # default: summarize latest 3
# npm run ai:last-change
#
# # ask a custom question:
# npm run ai:last-change -- "Summarize the last 3 repo changes and which files they touched"
#
# # increase / decrease how many items to feed
# npm run ai:last-change -- --limit 5
#
# # include JSON of the evidence (for automation)
# npm run ai:last-change -- --json
#
# # include more items (e.g., top 5)
# npm run ai:last-change -- --limit 5 --json

import os, json, subprocess, sqlite3, argparse, textwrap, difflib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, UTC, date
from openai import OpenAI

# ---------- Paths (reuse shared config) ----------
from conf import ROOT, SESSIONS_DIR, OUTBOX_DIR, DB_PATH, APPLIED_FILE
OUT_APPLIED = OUTBOX_DIR / APPLIED_FILE
SESS_DIR = SESSIONS_DIR  # keep local alias for existing references

# ---------- API config ----------
try:
    from conf import OPENAI_API_KEY, CHAT_MODEL
except ImportError:
    from conf import OPENAI_API_KEY, OPENAI_CHAT_MODEL as CHAT_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- Utils ----------
def iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()

def parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts).astimezone(UTC)
    except Exception:
        return None

def run(cmd: List[str]) -> str:
    return subprocess.check_output(cmd, cwd=str(ROOT), text=True).strip()

def model_supports_temperature(model: str) -> bool:
    lowered = model.lower()
    return not ("gpt-5" in lowered or "o1" in lowered)

def trim(s: Optional[str], n=600) -> str:
    if s is None:
        return ""
    s = s.strip()
    return s if len(s) <= n else s[:n] + " …[truncated]"

def diff_stats(prev: str, curr: str, sample_lines: int = 6) -> Tuple[int, int, str]:
    """
    Return (#added_lines, #removed_lines, sample_snippet_of_diff_additions)
    Uses a quick ndiff line-based summary for readability.
    """
    if prev is None:
        added = curr.splitlines()
        return len(added), 0, trim("\n".join(("+ " + ln) for ln in added[:sample_lines]), 600)

    added = removed = 0
    additions = []
    for ln in difflib.ndiff(prev.splitlines(), curr.splitlines()):
        if ln.startswith("+ "):
            added += 1
            if len(additions) < sample_lines:
                additions.append(ln)
        elif ln.startswith("- "):
            removed += 1
    snippet = trim("\n".join(additions), 600)
    return added, removed, snippet

# ---------- Collectors (with DETAILS) ----------
def latest_git_commits(n=3) -> List[Dict[str, Any]]:
    try:
        fmt = "%H|%ct|%an|%s"
        out = run(["git", "log", f"-{n}", f"--pretty=format:{fmt}"])
        rows = out.splitlines()
        events = []
        for row in rows:
            h, ts, author, msg = row.split("|", 3)
            dt = datetime.fromtimestamp(int(ts), UTC)
            files = run(["git", "diff-tree", "--no-commit-id", "--name-status", "-r", h]).splitlines()
            # Diffstat (concise)
            try:
                stat = run(["git", "show", "--stat", "--oneline", "-1", h])
            except Exception:
                stat = ""
            events.append({
                "source": "git",
                "ts": iso(dt),
                "commit": h,
                "author": author,
                "message": msg,
                "files": files[:50],
                "diffstat": trim(stat, 1200),
                "details": f"{msg}\n" + trim("\n".join(files), 600)
            })
        return events
    except Exception as e:
        return [{"source":"git","error":str(e)}]

def latest_applied_proposals(n=3) -> List[Dict[str, Any]]:
    if not OUT_APPLIED.exists():
        return []
    evs = []
    with OUT_APPLIED.open("r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try: j = json.loads(line)
            except Exception: continue
            if j.get("status") != "applied":
                continue
            evs.append({
                "source":"memory",
                "ts": j.get("ts"),
                "proposal_id": j.get("proposal_id"),
                "target": j.get("target"),
                "applied_items": j.get("applied_items", []),
                "note": j.get("note"),
                "details": " | ".join(j.get("applied_items", [])) or (j.get("note") or "")
            })
    evs = [e for e in evs if e.get("ts")]
    evs.sort(key=lambda x: parse_iso(x["ts"]) or datetime.min.replace(tzinfo=UTC), reverse=True)
    return evs[:n]

def latest_session_turns(n=3) -> List[Dict[str, Any]]:
    if not SESS_DIR.exists():
        return []
    files = sorted(SESS_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    evs = []
    for p in files[:max(n, 3)]:
        last_line = None
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                last_line = line
        if not last_line:
            continue
        try:
            j = json.loads(last_line)
        except Exception:
            continue
        msgs = j.get("messages", [])
        # extract last user + assistant texts for detail
        user_text = ""
        asst_text = ""
        for m in msgs:
            if m.get("role") == "user":
                user_text = m.get("content","")
            if m.get("role") == "assistant":
                asst_text = m.get("content","")
        evs.append({
            "source":"session",
            "file": p.name,
            "turn_id": j.get("turn_id"),
            "ts": j.get("ts"),
            "agent": j.get("agent"),
            "details": trim(f"Q: {user_text}\nA: {asst_text}", 1200)
        })
    evs = [e for e in evs if e.get("ts")]
    evs.sort(key=lambda x: parse_iso(x["ts"]) or datetime.min.replace(tzinfo=UTC), reverse=True)
    return evs[:n]

def _fetch_prev_revision(conn: sqlite3.Connection, source: str, kind: str, key: str, seq: int, rev: int) -> Optional[str]:
    """
    Load previous revision's content (rev-1) if it exists, else None.
    """
    prev = conn.execute(
        """
        SELECT content
        FROM chunks
        WHERE source=? AND kind=? AND key=? AND seq=? AND rev=?
        LIMIT 1
        """,
        (source, kind, key, seq, max(1, (rev or 1) - 1)),
    ).fetchone()
    if prev is None:
        # Try "max rev below current" in case revs are not strictly contiguous
        prev = conn.execute(
            """
            SELECT content
            FROM chunks
            WHERE source=? AND kind=? AND key=? AND seq=? AND rev < ?
            ORDER BY rev DESC
            LIMIT 1
            """,
            (source, kind, key, seq, rev or 1),
        ).fetchone()
    return None if prev is None else prev[0]

def latest_db_chunks(n=3) -> List[Dict[str, Any]]:
    """
    Use the revision-aware schema.
    Reads from chunks_head (latest, non-deleted) and computes a tiny diff vs previous revision.
    """
    if not DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA busy_timeout=3000")
        # Ensure the view exists; if not, fall back to base table newest updated rows.
        has_head = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='view' AND name='chunks_head'"
        ).fetchone() is not None

        if has_head:
            rows = conn.execute(
                """
                SELECT id, source, kind, key, seq, rev, updated_at, content
                FROM chunks_head
                WHERE updated_at IS NOT NULL
                ORDER BY datetime(updated_at) DESC
                LIMIT ?
                """,
                (n,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, source, kind, key, seq, rev, updated_at, content
                FROM chunks
                WHERE deleted_at IS NULL AND updated_at IS NOT NULL
                ORDER BY datetime(updated_at) DESC
                LIMIT ?
                """,
                (n,),
            ).fetchall()

        evs = []
        for id_, source, kind, key, seq, rev, ts, content in rows:
            prev_content = _fetch_prev_revision(conn, source, kind, key, seq, rev)
            add_lines, del_lines, sample = diff_stats(prev_content, content, sample_lines=6)
            delta_str = f"Δ +{add_lines}/-{del_lines}"
            details = f"{delta_str}\n" + (sample or trim(content, 600))
            evs.append({
                "source": "db",
                "ts": ts,
                "chunk_id": id_,
                "origin": source,
                "kind": kind,
                "key": key,
                "seq": seq,
                "rev": rev,
                "delta": delta_str,
                "details": details
            })
        conn.close()
        return evs
    except Exception as e:
        return [{"source":"db","error":str(e)}]

# ---------- LLM call ----------
def llm_summarize(question: str, unified_events: List[Dict,]):
    """
    Ask the model to pick/compose the best 'latest updates' answer from the unified events.
    """
    events_for_prompt = json.dumps(unified_events[:50], ensure_ascii=False, indent=0)

    system = (
        "You are a release/changes summarizer for a codebase. "
        "Given recent events (git commits, applied memory proposals, session turns, and DB recency), "
        "answer the user's question with precise, factual updates. Cite timestamps in short form. "
        "Prefer git and applied proposals for 'what changed' answers; include file hints or memory bullets if useful. "
        "Return: a concise answer (2–8 lines), then a 3-item bullet list."
    )
    user = (
        f"Question: {question}\n\n"
        f"Newest-first events (JSON):\n{events_for_prompt}\n\n"
        "Produce the answer now."
    )

    kwargs = {
        "model": CHAT_MODEL,
        "messages": [
            {"role":"system","content":system},
            {"role":"user","content":user}
        ]
    }
    if model_supports_temperature(CHAT_MODEL):
        kwargs["temperature"] = 0.2

    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content.strip()

# ---------- Sessions logging ----------
def append_session(question: str, answer: str):
    SESS_DIR.mkdir(parents=True, exist_ok=True)
    fpath = SESS_DIR / f"{date.today().isoformat()}.jsonl"
    turn_id = f"last-change-{datetime.now(UTC).strftime('%H%M%S%f')}"
    rec = {
        "ts": datetime.now(UTC).isoformat(),
        "turn_id": turn_id,
        "agent": "last-change",
        "messages": [
            {"role":"user","content":question},
            {"role":"assistant","content":answer}
        ]
    }
    with fpath.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return turn_id

# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(description="Summarize latest project changes (top N) with OpenAI and include detailed JSON.")
    ap.add_argument("--limit", type=int, default=3, help="How many latest items to include (default 3)")
    ap.add_argument("--json", action="store_true", help="Also print JSON of unified events (with details)")
    ap.add_argument("question", nargs="*", help="Optional question override")
    args = ap.parse_args()

    question = " ".join(args.question).strip() or "What are the latest changes and their impact?"
    n = max(1, min(args.limit, 10))

    git_evs = latest_git_commits(n)
    prop_evs = latest_applied_proposals(n)
    sess_evs = latest_session_turns(n)
    db_evs = latest_db_chunks(n)

    # unify by timestamp, newest first
    timeline: List[Dict[str, Any]] = []
    for ev in (git_evs + prop_evs + sess_evs + db_evs):
        ts = ev.get("ts")
        dt = parse_iso(ts) if ts else None
        if dt:
            ev["_ts_dt"] = dt
            timeline.append(ev)
    timeline.sort(key=lambda x: x["_ts_dt"], reverse=True)
    for ev in timeline:
        ev.pop("_ts_dt", None)

    unified_top = timeline[:n]

    # ask the model for a crisp answer based on unified evidence
    answer = llm_summarize(question, unified_top)

    # print the answer
    print("\n=== Latest Changes (Answer) ===\n")
    print(answer)

    # print evidence in human-friendly view
    print("\n--- Evidence (Newest First) ---\n")
    for i, ev in enumerate(unified_top, 1):
        src = ev.get("source")
        ts = ev.get("ts")
        if src == "git":
            print(f"{i}. [GIT] {ts}  {ev.get('message')}  by {ev.get('author')}  ({ev.get('commit')[:7]})")
            for ln in (ev.get("files") or [])[:5]:
                print("    ", ln)
        elif src == "memory":
            print(f"{i}. [MEMORY] {ts}  applied {ev.get('proposal_id')} → {ev.get('target')}")
            for it in (ev.get("applied_items") or [])[:5]:
                print("     -", it)
        elif src == "session":
            print(f"{i}. [SESSION] {ts}  turn {ev.get('turn_id')} ({ev.get('file')}) agent={ev.get('agent')}")
        elif src == "db":
            rev = ev.get("rev")
            delta = ev.get("delta")
            print(f"{i}. [DB] {ts}  {ev.get('origin')}#{ev.get('seq')} rev={rev} kind={ev.get('kind')} id={ev.get('chunk_id')[:10]}  {delta}")
        else:
            print(f"{i}. [{src}] {ts}")

    # JSON output (now with 'details' and 'delta')
    if args.json:
        print("\n--- JSON ---")
        print(json.dumps(unified_top, ensure_ascii=False, indent=2))

    # log to sessions
    append_session(question, answer)

if __name__ == "__main__":
    main()
