# ai-agent/bin/sync.py
import os, json, glob, sqlite3, hashlib, time
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Tuple, Optional
from contextlib import contextmanager

import yaml
import sqlite_vec
from sqlite_vec import serialize_float32
from openai import OpenAI

# ---- cross-platform single-writer lock helpers ----
# Prefer filelock (pure-Python, cross-platform). If unavailable, fall back:
_HAVE_FILELOCK = False
try:
    from filelock import FileLock, Timeout  # pip install filelock
    _HAVE_FILELOCK = True
except Exception:
    pass

if not _HAVE_FILELOCK:
    if os.name == "nt":
        import msvcrt  # Windows-only
    else:
        import fcntl  # POSIX

# Paths & config (reuse shared config instead of redefining)
from conf import (
    ROOT,
    DB_PATH,
    LOCK_PATH,
    SESSIONS_DIR,
    OPENAI_API_KEY,
    OPENAI_EMBED_MODEL,
)

SOURCE_STYLE = os.getenv("AI_AGENT_SOURCE_STYLE", "rel")  # "rel" or "base"
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- small utils ----------
def canonical_source(abs_path: str) -> str:
    try:
        rel = os.path.relpath(abs_path, ROOT)
    except Exception:
        rel = abs_path
    rel = rel.replace("\\", "/")
    return os.path.basename(abs_path) if SOURCE_STYLE == "base" else rel

@contextmanager
def single_writer_lock(path: str):
    """
    Cross-platform, non-blocking single-writer lock.

    Returns a context that yields a lock object (or file handle) when acquired,
    or None if another process holds the lock.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Preferred: filelock (works on mac/Linux/Windows)
    if _HAVE_FILELOCK:
        lock = FileLock(str(path))
        try:
            # tiny timeout -> effectively non-blocking
            lock.acquire(timeout=0.01)
        except Timeout:
            yield None
            return
        try:
            yield lock
        finally:
            try:
                lock.release()
            except Exception:
                pass
        return

    # Fallbacks if filelock is not installed
    if os.name == "nt":
        # Windows: use msvcrt.locking on a 1-byte region
        f = open(path, "a+")
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            f.close()
            yield None
            return
        try:
            yield f
        finally:
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
            f.close()
    else:
        # POSIX: use fcntl.flock like before
        f = open(path, "w")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError):
            f.close()
            yield None
            return
        try:
            yield f
        finally:
            try:
                fcntl.flock(f, fcntl.LOCK_UN)
            except OSError:
                pass
            f.close()

def sha1(s: str) -> str:
    return hashlib.sha1((s or "").encode("utf-8")).hexdigest()

def _norm(s: str) -> str:
    return " ".join((s or "").split()).strip()

def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None

def get_source_row(conn: sqlite3.Connection, source: str):
    return conn.execute("""
      SELECT source, kind, key, fingerprint, last_mtime, last_size, last_seq_processed, last_offset, updated_at
      FROM sources WHERE source=?
    """, (source,)).fetchone()

def set_meta(conn: sqlite3.Connection, key: str, value: str):
    conn.execute("""
      INSERT INTO meta(key,value) VALUES(?,?)
      ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))

# ---------- DB schema ----------
def ensure_db(conn: sqlite3.Connection):
    c = conn.cursor()
    c.execute("PRAGMA busy_timeout=5000;")
    try:
        c.execute("PRAGMA journal_mode=WAL;")
        c.execute("PRAGMA wal_autocheckpoint=1000;")
    except sqlite3.OperationalError:
        c.execute("PRAGMA journal_mode=DELETE;")
    c.execute("PRAGMA synchronous=NORMAL;")

    c.execute("""
    CREATE TABLE IF NOT EXISTS chunks(
      id          TEXT PRIMARY KEY,   -- c_xxx.rN (revisioned)
      source      TEXT,
      kind        TEXT,               -- memory_item | instruction_item | style_note | memory_yaml_meta | turn
      key         TEXT,               -- e.g. "module:sha16", "instructions:sha16", "style:sha16", "meta"
      seq         INTEGER,            -- 0 for YAML items/meta; 0..N for sessions
      rev         INTEGER,
      content     TEXT,
      chunk_hash  TEXT,
      updated_at  TEXT,
      deleted_at  TEXT
    )""")
    c.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_addr_rev
    ON chunks(source, kind, key, seq, rev)
    """)
    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_chunks_head_probe
    ON chunks(source, kind, key, seq, rev, deleted_at)
    """)

    try:
        c.execute("""
        CREATE VIEW IF NOT EXISTS chunks_head AS
        SELECT c.*
        FROM chunks c
        JOIN (
          SELECT source, kind, key, seq, MAX(rev) AS max_rev
          FROM chunks
          GROUP BY source, kind, key, seq
        ) h
          ON c.source=h.source AND c.kind=h.kind AND c.key=h.key AND c.seq=h.seq AND c.rev=h.max_rev
        WHERE c.deleted_at IS NULL
        """)
    except sqlite3.OperationalError as e:
        if "already exists" not in str(e).lower():
            raise

    c.execute("""
    CREATE TABLE IF NOT EXISTS sources(
      source              TEXT PRIMARY KEY,
      kind                TEXT NOT NULL,
      key                 TEXT NOT NULL,
      fingerprint         TEXT,
      last_mtime          TEXT,
      last_size           INTEGER,
      last_seq_processed  INTEGER,
      last_offset         INTEGER,
      updated_at          TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS meta(
      key   TEXT PRIMARY KEY,
      value TEXT
    )""")

    dims = 3072 if "text-embedding-3-large" in OPENAI_EMBED_MODEL else 1536
    cur = c.execute("SELECT value FROM meta WHERE key='embed_dims'").fetchone()
    current_dims = None if cur is None else cur[0]
    vec_exists = table_exists(conn, "vec_chunks")
    if (not vec_exists) or (current_dims != str(dims)):
        c.execute("DROP TABLE IF EXISTS vec_chunks")
        c.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
          chunk_id TEXT,
          embedding float[{dims}]
        )""")
        set_meta(conn, "embed_dims", str(dims))
    else:
        c.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
          chunk_id TEXT,
          embedding float[{dims}]
        )""")
    conn.commit()

# ---------- embeddings ----------
def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    res = client.embeddings.create(model=OPENAI_EMBED_MODEL, input=texts)
    return [d.embedding for d in res.data]

# ---------- revision logic ----------
def make_base_id(source: str, kind: str, key: str, seq: int) -> str:
    h = hashlib.sha1(f"{source}\x1f{kind}\x1f{key}\x1f{seq}".encode("utf-8")).hexdigest()
    return f"c_{h}"

def make_rev_id(base_id: str, rev: int) -> str:
    return f"{base_id}.r{rev}"

def get_head_row(conn: sqlite3.Connection, source: str, kind: str, key: str, seq: int):
    return conn.execute("""
        SELECT id, rev, content, chunk_hash, updated_at, deleted_at
        FROM chunks
        WHERE source=? AND kind=? AND key=? AND seq=?
        ORDER BY rev DESC
        LIMIT 1
    """, (source, kind, key, seq)).fetchone()

def upsert_revision_metadata(conn: sqlite3.Connection,
                             source: str, kind: str, key: str, seq: int,
                             content: str, content_hash: str, ts_iso: str):
    base_id = make_base_id(source, kind, key, seq)
    head = get_head_row(conn, source, kind, key, seq)
    cur = conn.cursor()

    if head is None:
        rev = 1
        cid = make_rev_id(base_id, rev)
        cur.execute("""
            INSERT INTO chunks (id, source, kind, key, seq, rev, content, chunk_hash, updated_at, deleted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """, (cid, source, kind, key, seq, rev, content, content_hash, ts_iso))
        return cid, rev, True

    head_id, head_rev, _hc, head_hash, _upd, head_deleted = head
    if head_deleted is not None or head_hash != content_hash:
        rev = (head_rev or 0) + 1
        cid = make_rev_id(base_id, rev)
        cur.execute("""
            INSERT INTO chunks (id, source, kind, key, seq, rev, content, chunk_hash, updated_at, deleted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """, (cid, source, kind, key, seq, rev, content, content_hash, ts_iso))
        return cid, rev, True

    cur.execute("UPDATE chunks SET updated_at=? WHERE id=?", (ts_iso, head_id))
    return head_id, head_rev, False

def insert_vector(conn: sqlite3.Connection, chunk_id: str, emb: List[float]):
    conn.execute("DELETE FROM vec_chunks WHERE chunk_id=?", (chunk_id,))
    conn.execute("INSERT INTO vec_chunks(chunk_id, embedding) VALUES(?,?)",
                 (chunk_id, serialize_float32(emb)))

def soft_delete_missing_keys(conn: sqlite3.Connection, source: str, kind: str,
                             keep_keys: List[str], ts_iso: str):
    if not keep_keys:
        conn.execute("""
          UPDATE chunks
             SET deleted_at=?
           WHERE source=? AND kind=?
             AND deleted_at IS NULL
             AND rev = (SELECT MAX(rev) FROM chunks c2
                        WHERE c2.source=chunks.source AND c2.kind=chunks.kind
                          AND c2.key=chunks.key AND c2.seq=chunks.seq)
        """, (ts_iso, source, kind))
        return
    qmarks = ",".join("?" for _ in keep_keys)
    conn.execute(f"""
      UPDATE chunks
         SET deleted_at=?
       WHERE source=? AND kind=?
         AND deleted_at IS NULL
         AND (key) NOT IN ({qmarks})
         AND rev = (SELECT MAX(rev) FROM chunks c2
                    WHERE c2.source=chunks.source AND c2.kind=chunks.kind
                      AND c2.key=chunks.key AND c2.seq=chunks.seq)
    """, (ts_iso, source, kind, *keep_keys))

# ---------- sources state helpers ----------
def upsert_source_yaml(conn: sqlite3.Connection, source: str, key: str,
                       fingerprint: str, mtime_iso: str, size: int):
    conn.execute("""
      INSERT INTO sources(source, kind, key, fingerprint, last_mtime, last_size, last_seq_processed, last_offset, updated_at)
      VALUES(?,?,?,?,?,?,NULL,NULL,?)
      ON CONFLICT(source) DO UPDATE SET
        kind=excluded.kind,
        key=excluded.key,
        fingerprint=excluded.fingerprint,
        last_mtime=excluded.last_mtime,
        last_size=excluded.last_size,
        updated_at=excluded.updated_at
    """, (source, "yaml", key, fingerprint, mtime_iso, size, datetime.now(UTC).isoformat()))

def upsert_source_jsonl_state(conn: sqlite3.Connection, source: str, key: str,
                              mtime_iso: str, size: int, last_seq: int, last_offset: int):
    conn.execute("""
      INSERT INTO sources(source, kind, key, fingerprint, last_mtime, last_size, last_seq_processed, last_offset, updated_at)
      VALUES(?,?,?,?,?,?,?,?,?)
      ON CONFLICT(source) DO UPDATE SET
        kind=excluded.kind,
        key=excluded.key,
        last_mtime=excluded.last_mtime,
        last_size=excluded.last_size,
        last_seq_processed=excluded.last_seq_processed,
        last_offset=excluded.last_offset,
        updated_at=excluded.updated_at
    """, (source, "turn", key, None, mtime_iso, size, last_seq, last_offset, datetime.now(UTC).isoformat()))

# ---------- YAML item-ingestors (NO slicing) ----------
def _compute_items_fingerprint(items: List[Tuple[str, str]]) -> str:
    payload = "\n".join(f"{k}|{sha1(v)}" for (k, v) in sorted(items, key=lambda x: x[0]))
    return sha1(payload)

def _ingest_item_list(conn: sqlite3.Connection, source: str, kind: str,
                      items: List[Tuple[str, str]], mtime_iso: str, file_key: str, file_size: int):
    fp = _compute_items_fingerprint(items)
    prev = get_source_row(conn, source)
    if prev and prev[3] == fp:
        print(f"skip (unchanged): {source} [{kind}]")
        return

    to_embed: List[Tuple[str, str]] = []
    keep_keys = [k for (k, _t) in items]

    cur = conn.cursor()
    cur.execute("BEGIN IMMEDIATE")
    try:
        for key, text in items:
            text = _norm(text)
            if not text:
                continue
            chash = sha1(text)
            cid, _rev, needs = upsert_revision_metadata(conn, source, kind, key, 0, text, chash, mtime_iso)
            if needs:
                to_embed.append((cid, text))

        soft_delete_missing_keys(conn, source, kind, keep_keys, mtime_iso)
        upsert_source_yaml(conn, source, file_key, fp, mtime_iso, file_size)

        if to_embed:
            texts = [t for (_cid, t) in to_embed]
            vecs = embed_texts(texts)
            for (cid, _t), emb in zip(to_embed, vecs):
                insert_vector(conn, cid, emb)

        conn.commit()
        print(f"ingested {kind}: {source} (items={len(items)}, embed={len(to_embed)})")
    except Exception:
        conn.rollback()
        raise

def ingest_memory_items(conn: sqlite3.Connection, fname="memory.yaml"):
    path = os.path.join(ROOT, fname)
    if not os.path.exists(path):
        return
    source = canonical_source(path)
    st = Path(path).stat()
    mtime_iso = datetime.fromtimestamp(st.st_mtime, UTC).isoformat()

    try:
        y = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"[warn] cannot parse {fname}: {e}")
        return

    modules = y.get("memory_modules") or {}
    items: List[Tuple[str, str]] = []

    if isinstance(modules, dict) and modules:
        for mod, lst in modules.items():
            if not isinstance(lst, list):
                continue
            for txt in lst:
                if not isinstance(txt, str):
                    continue
                txt_n = _norm(txt)
                if not txt_n:
                    continue
                key = f"{_norm(mod).lower()}:{sha1(txt_n)[:16]}"
                items.append((key, txt_n))
    else:
        legacy = y.get("memory_log")
        if isinstance(legacy, list):
            for txt in legacy:
                if not isinstance(txt, str):
                    continue
                txt_n = _norm(txt)
                if not txt_n:
                    continue
                key = f"general:{sha1(txt_n)[:16]}"
                items.append((key, txt_n))

    _ingest_item_list(conn, source, "memory_item", items, mtime_iso, fname, st.st_size)

# ---- non-item meta snapshot for memory.yaml (no slicing; excludes memory_modules) ----
import copy as _copy
def _yaml_meta_text(yobj: dict) -> str:
    y2 = _copy.deepcopy(yobj or {})
    y2.pop("memory_modules", None)
    y2.pop("memory_log", None)  # exclude legacy to avoid duplication
    return yaml.safe_dump(y2, sort_keys=True, allow_unicode=True).strip()

def ingest_memory_meta(conn: sqlite3.Connection, fname="memory.yaml"):
    path = os.path.join(ROOT, fname)
    if not os.path.exists(path):
        return
    source = canonical_source(path)
    st = Path(path).stat()
    mtime_iso = datetime.fromtimestamp(st.st_mtime, UTC).isoformat()

    try:
        y = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"[warn] cannot parse {fname} for meta snapshot: {e}")
        return

    text = _yaml_meta_text(y)
    if not text:
        conn.execute("""
          UPDATE chunks SET deleted_at=?
           WHERE source=? AND kind='memory_yaml_meta' AND key='meta' AND seq=0
             AND deleted_at IS NULL
             AND rev = (SELECT MAX(rev) FROM chunks c2
                        WHERE c2.source=chunks.source AND c2.kind=chunks.kind
                          AND c2.key=chunks.key AND c2.seq=chunks.seq)
        """, (mtime_iso, source))
        conn.commit()
        return

    chash = sha1(text)
    cid, _rev, needs = upsert_revision_metadata(conn, source, "memory_yaml_meta", "meta", 0, text, chash, mtime_iso)
    if needs:
        vec = embed_texts([text])[0]
        insert_vector(conn, cid, vec)
    print(f"ingested memory_yaml_meta: {source} (changed={needs})")

def ingest_instruction_items(conn: sqlite3.Connection, fname="instructions.yaml"):
    path = os.path.join(ROOT, fname);  source = canonical_source(path)
    if not os.path.exists(path):
        return
    st = Path(path).stat()
    mtime_iso = datetime.fromtimestamp(st.st_mtime, UTC).isoformat()
    try:
        y = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"[warn] cannot parse {fname}: {e}");  return

    items: List[Tuple[str, str]] = []
    lst = y.get("instructions")
    if isinstance(lst, list):
        for txt in lst:
            if not isinstance(txt, str): continue
            txt_n = _norm(txt)
            if not txt_n: continue
            key = f"instructions:{sha1(txt_n)[:16]}"
            items.append((key, txt_n))
    _ingest_item_list(conn, source, "instruction_item", items, mtime_iso, fname, st.st_size)

def ingest_style_notes(conn: sqlite3.Connection, fname="style.yaml"):
    path = os.path.join(ROOT, fname);  source = canonical_source(path)
    if not os.path.exists(path):
        return
    st = Path(path).stat()
    mtime_iso = datetime.fromtimestamp(st.st_mtime, UTC).isoformat()
    try:
        y = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"[warn] cannot parse {fname}: {e}");  return

    items: List[Tuple[str, str]] = []
    style = y.get("style") or {}
    notes = style.get("notes")
    if isinstance(notes, list):
        for txt in notes:
            if not isinstance(txt, str): continue
            txt_n = _norm(txt)
            if not txt_n: continue
            key = f"style:{sha1(txt_n)[:16]}"
            items.append((key, txt_n))
    _ingest_item_list(conn, source, "style_note", items, mtime_iso, fname, st.st_size)

# ---------- sessions (unchanged) ----------
def chunk_text(s: str, max_chars=2000) -> List[str]:
    s = (s or "").strip()
    if not s:
        return []
    out, buf, total = [], [], 0
    for para in s.split("\n"):
        if total + len(para) + 1 > max_chars and buf:
            out.append("\n".join(buf).strip()); buf=[]; total=0
        buf.append(para); total += len(para) + 1
    if buf:
        out.append("\n".join(buf).strip())
    return out

def ingest_sessions(conn: sqlite3.Connection):
    session_glob = os.path.join(str(SESSIONS_DIR), "*.jsonl")
    for p in glob.glob(session_glob):
        source = canonical_source(p)
        key = os.path.basename(p)
        st = Path(p).stat()
        size, mtime_iso = st.st_size, datetime.fromtimestamp(st.st_mtime, UTC).isoformat()

        prev = get_source_row(conn, source)
        last_offset = 0;  last_seq = -1;  reset_all = False
        if prev:
            _s, _k, _key, _fp, _lm, last_size, prev_seq, prev_off, _upd = prev
            last_offset = prev_off or 0
            last_seq = prev_seq if prev_seq is not None else -1
            if last_size is not None and size < int(last_size):
                reset_all = True; last_offset = 0; last_seq = -1

        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        try:
            if reset_all:
                cur.execute("""
                  UPDATE chunks SET deleted_at=?
                  WHERE source=? AND kind='turn' AND deleted_at IS NULL
                    AND rev = (SELECT MAX(rev) FROM chunks c2
                               WHERE c2.source=chunks.source AND c2.kind=chunks.kind
                                 AND c2.key=chunks.key AND c2.seq=chunks.seq)
                """, (mtime_iso, source))

            with open(p, "r", encoding="utf-8") as f:
                f.seek(last_offset)
                seq_counter = last_seq + 1
                to_embed: List[Tuple[str, str]] = []

                for line in f:
                    if not line.strip():
                        seq_counter += 1;  continue
                    try:
                        j = json.loads(line)
                    except Exception:
                        seq_counter += 1;  continue

                    msgs = j.get("messages", [])
                    text = "\n".join([m.get("content", "") for m in msgs]).strip()
                    if not text:
                        seq_counter += 1;  continue

                    ts = j.get("ts")
                    if ts:
                        try:
                            ts_dt = datetime.fromisoformat(ts.replace("Z","+00:00"))
                        except Exception:
                            ts_dt = datetime.now(UTC)
                    else:
                        ts_dt = datetime.fromtimestamp(Path(p).stat().st_mtime, UTC)
                    ts_iso = ts_dt.isoformat()

                    parts = chunk_text(text, 2000)
                    for idx, part in enumerate(parts):
                        chash = sha1(part)
                        cid, _rev, needs = upsert_revision_metadata(conn, source, "turn", j.get("turn_id", str(seq_counter)), idx, part, chash, ts_iso)
                        if needs:
                            to_embed.append((cid, part))
                    seq_counter += 1

                if to_embed:
                    texts = [t[1] for t in to_embed]
                    vectors = embed_texts(texts)
                    for (cid, _), emb in zip(to_embed, vectors):
                        insert_vector(conn, cid, emb)

                new_offset = f.tell()
                upsert_source_jsonl_state(conn, source, key, mtime_iso, size, seq_counter - 1, new_offset)

            conn.commit()
            print(f"ingested sessions: {key} (new_seq={max(seq_counter-1, -1)}, embed={len(to_embed)})")
        except Exception:
            conn.rollback()
            raise

# ---------- main ----------
def main():
    with single_writer_lock(str(LOCK_PATH)) as lock_obj:
        if lock_obj is None:
            print("sync: another process is running; skipping this cycle.")
            return

        db_dir = os.path.dirname(str(DB_PATH)) or "."
        os.makedirs(db_dir, exist_ok=True)

        probe = os.path.join(db_dir, f".sqlite_write_probe.{os.getpid()}.{int(time.time()*1e6)}")
        try:
            with open(probe, "wb") as fh:
                fh.write(b"ok")
        finally:
            try: os.remove(probe)
            except FileNotFoundError: pass

        db = sqlite3.connect(str(DB_PATH), isolation_level=None)
        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)

        ensure_db(db)

        # YAML: per-item + a single meta snapshot (no slicing)
        ingest_memory_items(db, "memory.yaml")
        ingest_memory_meta(db, "memory.yaml")
        ingest_instruction_items(db, "instructions.yaml")
        ingest_style_notes(db, "style.yaml")

        # Sessions unchanged
        ingest_sessions(db)

        print(f"SYNC complete → knowledge.db updated. {datetime.now(UTC)}")

if __name__ == "__main__":
    main()
