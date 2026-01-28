#!/usr/bin/env python3

"""
# start llama server
python ai-agent/py/src/llama_cpp_server_start.py --llama-server cpp  --n-thread 6 --gpu-layers -1 --n-batch 1024 --ctx-size 0

ctx: 4096, 8192, 16384, 32768
--n-threads: -1 or number of cpu core in our case 6 max
--n-gpu-layers: -1 (offload all layers best GPU use). or number of gpu layers 20, 32

--n-batch
Default: 256
Batch size for feeding tokens.
Higher → faster prompt ingestion (if VRAM allows).
Too high → GPU out of memory.
Try 256-512 on 16 GB VRAM, adjust if needed.

"""

import sys, os, argparse, subprocess, time, json, webbrowser, socket
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from pathlib import Path

import conf as cfg  # expects: AI_MODELS_DIR, LLAMA_B6317_BIN, etc.

# ===================== EDIT THIS LIST =====================
# 'rel' can be relative to AI_MODELS_DIR or an absolute path; 'chat_format' is optional.
MODELS = [
    # {"rel": "unsloth/Qwen3-4B-Thinking-2507-GGUF/Qwen3-4B-Thinking-2507-IQ4_XS.gguf", "chat_format": "qwen"},
    # {"rel": "unsloth/Qwen3-8B-128K-GGUF/Qwen3-8B-128K-IQ4_XS.gguf", "chat_format": "qwen"},
    # {"rel": "unsloth/Qwen3-14B-GGUF/Qwen3-14B-IQ4_XS.gguf", "chat_format": "qwen"},
     {"rel": "unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF/Qwen3-Coder-30B-A3B-Instruct-IQ4_XS.gguf", "chat_format": "qwen"},
    # {"rel": "unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF/Qwen3-Coder-30B-A3B-Instruct-UD-IQ3_XXS.gguf", "chat_format": "qwen"},
    # {"rel": "unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF/Qwen3-Coder-30B-A3B-Instruct-UD-IQ2_M.gguf", "chat_format": "qwen"},
    # {"rel": "unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF/Qwen3-Coder-30B-A3B-Instruct-UD-IQ1_M.gguf", "chat_format": "qwen"},
    # {"rel": "unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF/Qwen3-Coder-30B-A3B-Instruct-UD-IQ1_S.gguf", "chat_format": "qwen"},

    # {"rel": "google/gemma-3-4b-it-qat-q4_0-gguf/gemma-3-4b-it-q4_0.gguf", "chat_format": "gemma"},
    
    # {"rel": "Qwen/Qwen3-8B-GGUF/Qwen3-8B-Q8_0.gguf", "chat_format": "qwen"},
    # {"rel": "Qwen/Qwen3-14B-GGUF/Qwen3-14B-Q8_0.gguf", "chat_format": "qwen"},
    
    # {"rel": "bartowski/nvidia_NVIDIA-Nemotron-Nano-9B-v2-GGUF/nvidia_NVIDIA-Nemotron-Nano-9B-v2-Q8_0.gguf", "chat_format": "llama-2"},
    # {"rel": "bartowski/nvidia_NVIDIA-Nemotron-Nano-9B-v2-GGUF/nvidia_NVIDIA-Nemotron-Nano-9B-v2-IQ4_XS.gguf", "chat_format": "llama-2"},
    # {"rel": "bartowski/nvidia_NVIDIA-Nemotron-Nano-12B-v2-GGUF/nvidia_NVIDIA-Nemotron-Nano-12B-v2-Q8_0.gguf", "chat_format": "llama-2"},
    # {"rel": "bartowski/nvidia_NVIDIA-Nemotron-Nano-12B-v2-GGUF/nvidia_NVIDIA-Nemotron-Nano-12B-v2-IQ4_XS.gguf", "chat_format": "llama-2"},
    # {"rel": "bartowski/nvidia_NVIDIA-Nemotron-Nano-12B-v2-GGUF/nvidia_NVIDIA-Nemotron-Nano-12B-v2-Q5_K_M.gguf", "chat_format": "llama-2"},
    # {"rel": "bartowski/Qwen_Qwen3-14B-GGUF/Qwen_Qwen3-14B-IQ4_XS.gguf", "chat_format": "qwen"},
    
    # {"rel": "ggml-org/gpt-oss-20b-GGUF/gpt-oss-20b-mxfp4.gguf", "chat_format": "llama-2"},
]
# Optional: set a persistent WebUI data dir (Windows example). Change for Linux if needed.
WEBUI_DATA_DIR = r"C:\Users\Admin\Documents\open-webui\data"
# =========================================================

# ---------- health / utility ----------
def _wait_for(url: str, ok_predicate, timeout_s: int = 180, name: str = "service"):
    start = time.time()
    last_err = None
    while time.time() - start < timeout_s:
        try:
            with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=5) as r:
                body = r.read()
                if ok_predicate(r, body):
                    return True
        except (URLError, HTTPError, TimeoutError, ConnectionRefusedError) as e:
            last_err = e
        time.sleep(0.5)
    if last_err:
        print(f"[warn] timeout waiting for {name}: {url}  last error: {last_err}", file=sys.stderr)
    else:
        print(f"[warn] timeout waiting for {name}: {url}", file=sys.stderr)
    return False

def _is_llama_ready(resp, body_bytes):
    if resp.status != 200:
        return False
    try:
        data = json.loads(body_bytes.decode("utf-8"))
        return isinstance(data, dict) and isinstance(data.get("data"), list) and len(data["data"]) >= 1
    except Exception:
        return False

def _is_webui_healthy(resp, _body_bytes):
    return resp.status == 200

def _which(cmd: str):
    from shutil import which
    return which(cmd)

def _candidate_webui_paths():
    paths = []
    for name in ("open-webui.exe", "open-webui"):
        w = _which(name)
        if w:
            paths.append(w)
    user = os.environ.get("USERPROFILE") or ""
    appdata = os.environ.get("APPDATA") or ""
    guesses = [
        os.path.join(appdata, "Python", "Python312", "Scripts", "open-webui.exe"),
        os.path.join(appdata, "Python", "Python311", "Scripts", "open-webui.exe"),
        os.path.join(user, "AppData", "Roaming", "Python", "Python312", "Scripts", "open-webui.exe"),
        os.path.join(user, "AppData", "Roaming", "Python", "Python311", "Scripts", "open-webui.exe"),
    ]
    for g in guesses:
        if g and os.path.isfile(g):
            paths.append(g)
    # dedupe
    out, seen = [], set()
    for p in paths:
        if p not in seen:
            out.append(p); seen.add(p)
    return out

def _find_free_port(start_port: int, host: str = "127.0.0.1"):
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return port
            except OSError:
                port += 1

def _shutdown(servers, ui_proc, router_proc):
    for s in servers:
        p = s["proc"]
        if p and p.poll() is None:
            try: p.terminate(); p.wait(timeout=5)
            except Exception: p.kill()
    if router_proc and router_proc.poll() is None:
        try: router_proc.terminate(); router_proc.wait(timeout=5)
        except Exception: router_proc.kill()
    if ui_proc and ui_proc.poll() is None:
        try: ui_proc.terminate(); ui_proc.wait(timeout=5)
        except Exception: ui_proc.kill()

# ---- NEW: resolve C++ llama.cpp server from conf.LLAMA_B6317_BIN (file or dir) ----
def _resolve_cpp_server_from_conf() -> str | None:
    """
    Reads cfg.LLAMA_B6317_BIN:
      - if it's a FILE, returns it
      - if it's a DIR, searches for server(.exe) inside
      - else returns None
    """
    p = getattr(cfg, "LLAMA_B6317_BIN", None)
    if not p:
        return None
    p = Path(p)
    print(f"LLAMA_B6317_BIN: {p}")
    if p.is_file():
        return str(p)
    if p.is_dir():
        for name in ("llama-server.exe", "server"):
            cand = p / name
            if cand.exists() and cand.is_file():
                return str(cand)
    return None

# ---------- main ----------
def main():
    default_threads = max(1, (os.cpu_count() or 8) - 1)

    ap = argparse.ArgumentParser(description="Start one llama.cpp server per model + Open WebUI (always).")
    # Llama servers (multi-model)
    ap.add_argument("--host", default="127.0.0.1", help="Host for llama servers")
    ap.add_argument("--base-port", type=int, default=8080, help="First llama server port; others auto-increment")
    ap.add_argument("--ctx-size", default="4096", help="Context tokens per model server")
    ap.add_argument("--gpu-layers", dest="gpu_layers", default="-1",
                    help="-1 = offload all layers to GPU if possible; else number of layers")
    ap.add_argument("--n-thread", type=int, default=default_threads,
                    help=f"CPU threads for inference (default {default_threads})")
    ap.add_argument("--n-batch", type=int, default=256, help="Prompt batch size per server")

    # Server backend selection: python (default) or c++
    ap.add_argument("--llama-server", default="python", choices=["python", "c++", "cpp"],
                    help="Which backend to use for each model server. Default: python")

    # WebUI (always on)
    ap.add_argument("--webui-host", default="127.0.0.1", help="Host for Open WebUI")
    ap.add_argument("--webui-port", default="3000", help="Port for Open WebUI")
    ap.add_argument("--open-webui-cmd", default=None, help="Full path to open-webui executable")
    ap.add_argument("--no-open-browser", action="store_true", help="Do not open the browser automatically")

    args = ap.parse_args()

    base_dir: Path = Path(cfg.AI_MODELS_DIR).expanduser().resolve()

    # Resolve each model path explicitly (no scanning)
    ggufs: list[tuple[Path, str | None]] = []
    for m in MODELS:
        rel = m["rel"]
        chatfmt = m.get("chat_format")
        p = Path(rel)
        model_path = p if p.is_absolute() else (base_dir / p)
        if not model_path.exists():
            print(f"[ERROR] Model file not found: {model_path}", file=sys.stderr)
            sys.exit(1)
        ggufs.append((model_path, chatfmt))

    print(f"[startup] AI_MODELS_DIR : {base_dir}")
    print(f"[startup] Using {len(ggufs)} models:")
    for p, chatfmt in ggufs:
        print(f"  - {p}    chat_format={chatfmt or 'auto'}")

    env = os.environ.copy()
    env.setdefault("AI_MODELS_DIR", str(base_dir))

    # Decide backend
    server_choice = args.llama_server.lower()
    use_cpp = True if server_choice in ("c++", "cpp") else False

    cpp_server = None
    if use_cpp:
        cpp_server = _resolve_cpp_server_from_conf()
        if not cpp_server:
            print("[error] --llama-server cpp selected, but conf.LLAMA_B6317_BIN did not resolve to a server binary.", file=sys.stderr)
            print("        Set LLAMA_B6317_BIN to a file (server/server.exe) or a dir containing it.")
            sys.exit(2)
        print(f"[info] Using C++ llama.cpp server: {cpp_server}")
    else:
        print("[info] Using python backend: python -m llama_cpp.server")

    # 2) Launch one model server per model (embeddings always ON)
    servers = []
    next_port = int(args.base_port)
    for model_path, chat_format in ggufs:
        port = _find_free_port(next_port, args.host)
        next_port = port + 1
        alias = model_path.name

        if use_cpp:
            # --- C++ llama.cpp server (b6317+) ---
            # Flags: -m model, -c ctx, -ngl n_gpu_layers, -t threads, -b n_batch, --embedding, --host, --port
            srv_cmd = [
                cpp_server,
                "-m", str(model_path),
                "--host", str(args.host), 
                "--port", str(port),
                "-c", str(args.ctx_size),
                "-ngl", str(args.gpu_layers),
                "-t", str(args.n_thread),
                "-b", str(args.n_batch),
                "-a", alias,
                #"-np", "24", 
                #"-ub", "64",
                #"--cache-type-k", "iq4_nl",
                #"--cache-type-v", "iq4_nl",
                #"--cont-batching", "off",
                "--context-shift",
                #"--no-pinned", # (not working) to avoid large pinned host buffers (some perf cost)
                "--no-mmap", # server reads the whole model into RAM up front (no paging during inference). Helps if you have enough free RAM to keep the full model + KV cache resident.
                #"--mlock", # (not working) allows the model to be loaded lazily (consumed slowly) but guarantees that once a part of the model is in RAM, it will not be swapped out. Uses the default mmap lazy loading to bring model pages into RAM only when they are first needed. It then ensures that once those pages are in RAM, they stay there. This shifts the loading cost from startup to the first time each model component is used, with a benefit of permanently avoiding disk-based pageouts for the locked pages thereafter
                #"--no-nccl", # multi-GPU collective communication. We have only 1 GPU (most Windows/single-GPU CUDA builds don’t expose NCCL options at all)
                "--flash-attn", # FlashAttention is a highly specialized kernel that requires a minimum NVIDIA compute capability of 7.5 (Turing architecture) for FlashAttention v1 and 8.0+ (Ampere, Ada, or Hopper architecture) for FlashAttention v2
                #"--embedding",
                "--jinja",
            ]
            launch_desc = "llama.cpp C++ server"
            # NOTE: C++ server auto-uses model’s template; no --chat_format here.
        else:
            # --- Python backend (llama-cpp-python) ---
            srv_cmd = [
                sys.executable, 
                "-m", "llama_cpp.server",
                "--model", str(model_path),
                "--host", str(args.host), 
                "--port", str(port),
                "--n_ctx", str(args.ctx_size),
                "--n_gpu_layers", str(args.gpu_layers),
                "--n_threads", str(args.n_thread),
                "--n_batch", str(args.n_batch),
                "--model_alias", alias,
                "--cont-batching",
                "--context-shift",
                "--embedding", "true"
            ]
            if chat_format:
                srv_cmd.extend(["--chat_format", chat_format])
            launch_desc = "llama-cpp-python server"

        print(f"[startup] launching {launch_desc} for {alias} on http://{args.host}:{port} …")
        proc = subprocess.Popen(srv_cmd, env=env)
        servers.append({"proc": proc, "alias": alias, "port": port, "chat_format": chat_format})

    # 3) Wait for each server readiness at /v1/models
    for s in servers:
        url = f"http://{args.host}:{s['port']}/v1/models"
        if _wait_for(url, _is_llama_ready, timeout_s=240, name=f"llama server ({s['alias']})"):
            print(f"[ok] {s['alias']} ready → {url}")
        else:
            print(f"[warn] {s['alias']} did not report ready: {url}")

    # 4) Router (single URL on :9000)
    router_cfg_path = os.path.join(os.path.expanduser("~"), ".openai_router", "router_config.json")
    os.makedirs(os.path.dirname(router_cfg_path), exist_ok=True)
    routes = { s["alias"]: f"http://{args.host}:{s['port']}/v1" for s in servers }
    with open(router_cfg_path, "w", encoding="utf-8") as f:
        json.dump({"routes": routes}, f, indent=2)

    router_host, router_port = "127.0.0.1", 9000
    router_cmd = [sys.executable, str(Path(__file__).with_name("openai_router.py")),
                  "--host", router_host, "--port", str(router_port),
                  "--config", router_cfg_path]
    print(f"[startup] launching OpenAI router on http://{router_host}:{router_port}/v1")
    router = subprocess.Popen(router_cmd, env=env)

    # 5) Start Open WebUI (always)
    if args.open_webui_cmd:
        cmd = [args.open_webui_cmd, "serve", "--host", args.webui_host, "--port", str(args.webui_port)]
    else:
        cand = _candidate_webui_paths()
        if not cand:
            print("[error] Could not find 'open-webui' executable. Install it or pass --open-webui-cmd.", file=sys.stderr)
            _shutdown(servers, None, router)
            sys.exit(2)
        cmd = [cand[0], "serve", "--host", args.webui_host, "--port", str(args.webui_port)]

    openai_api_base = f"http://{router_host}:{router_port}/v1"   # single URL for WebUI

    # 6) DATA_DIR (change for Linux if needed)
    data_dir = WEBUI_DATA_DIR or os.path.join(os.path.expanduser("~"), ".open-webui", "data")
    os.makedirs(data_dir, exist_ok=True)

    ui_env = env.copy()
    ui_env["DATA_DIR"] = data_dir
    ui_env.setdefault("OPENAI_API_BASE_URL", openai_api_base)
    ui_env.setdefault("OPENAI_API_KEY", "sk-local")
    ui_env.setdefault("DEFAULT_MODELS", ",".join(s["alias"] for s in servers))

    print(f"[startup] launching Open WebUI… ({cmd[0]})")
    ui = subprocess.Popen(cmd, env=ui_env)

    webui_health = f"http://{args.webui_host}:{args.webui_port}/health"
    if _wait_for(webui_health, _is_webui_healthy, timeout_s=120, name="open-webui"):
        print(f"[ok] Open WebUI → http://{args.webui_host}:{args.webui_port}")
        if not args.no_open_browser:
            try: webbrowser.open(f"http://{args.webui_host}:{args.webui_port}")
            except Exception as e: print(f"[warn] could not open browser: {e}")
    else:
        print(f"[warn] Open WebUI not healthy yet: {webui_health}")

    if len(servers) > 1:
        print("\n[howto] Add backends in WebUI → Settings → Connections → OpenAI Connections (if needed):")
        for s in servers:
            print(f"  base_url = http://{args.host}:{s['port']}/v1   (models show as: {s['alias']})")

    try:
        ui.wait()
    except KeyboardInterrupt:
        pass
    finally:
        _shutdown(servers, ui, router)

if __name__ == "__main__":
    main()