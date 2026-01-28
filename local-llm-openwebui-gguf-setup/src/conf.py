# ai-agent/config.py
import os, sys
from pathlib import Path

def _default_dir() -> Path:
    """
    Returns the default path for AI models based on the operating system.
    """
    system = sys.platform
    
    if system == "win32":
        # Returns C:\Users\YourUsername\ai\models on Windows
        # return Path.home() / "ai" / "models"
        # return Path("D:/ai") # Windows
        return Path("C:/Users/Admin/Documents/ai") # switchin to NVME storage for better performance
    elif system == "darwin":
        # Returns /Users/YourUsername/ai/models on macOS
        return Path.home() / "ai"
    else:  # Assumes Linux or other Unix-like OS
        # Returns /home/YourUsername/ai/models on Linux
        return Path.home() / "ai"


ROOT = Path(__file__).resolve().parents[2]   # -> .../ai-agent
DB_PATH = ROOT / "knowledge.db"
LOCK_PATH = ROOT / "knowledge.db.lock"
SESSIONS_DIR = ROOT / "sessions"
INBOX_DIR = ROOT / "inbox"
OUTBOX_DIR = ROOT / "outbox"
PROPOSALS_FILE = "proposals.jsonl"
APPLIED_FILE = "applied.jsonl"
ERRORS_FILE = "errors.jsonl"

# _env = os.getenv("AI_MODELS_DIR")
# if _env:
#     AI_MODELS_DIR = Path(_env).expanduser().resolve()
# else:
#     AI_MODELS_DIR = (Path(_default_dir()) / "models").expanduser().resolve()

AI_MODELS_DIR = (Path(_default_dir()) / "models").expanduser().resolve()

LLAMA_B6317_BIN = (Path(_default_dir()) / "llama-b6317-bin-win-cuda-12.4-x64").expanduser().resolve()

# Prefer environment variable; fallback to hardcoded for local dev if you want
OPENAI_API_KEY = ""

# Embeddings model (high-accuracy, 3072-dim vectors)
OPENAI_EMBED_MODEL = "text-embedding-3-large" # or text-embedding-3-small

# Chat/completions model (GPT-5 family)
OPENAI_CHAT_MODEL = "gpt-5-mini"

# Test mode flag
TEST_MODE = True

