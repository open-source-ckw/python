# libs/conf/conf_loader.py
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv, dotenv_values
import typed_settings as ts
from libs.conf.setting import ConfSetting

# env overwrite sequence is: [defaults (if any) > other config > .env > x.env > system env ]

class ConfLoader:
    """
    Effective precedence (low -> high):
      defaults
      < env/base.{toml|yaml|yml} < other env/*.{toml|yaml|yml} (alphabetical) < env/<PY_ENV>.{toml|yaml|yml}
      < env/.env < env/<PY_ENV>.env < real OS environment
    """

    # --- paths ---
    @staticmethod
    def _repo_root() -> Path:
        # file is libs/conf/conf_loader.py  -> parents[2] is repo root (libs -> <root>)
        return Path(__file__).resolve().parents[2]

    # --- which overlay to use ---
    @staticmethod
    def _resolve_py_env(repo_root: Path) -> Optional[str]:
        """
        Highest priority selector for overlay name:
          1) OS env: PY_ENV   (servers can set this, no git changes)
          2) Fallback: value in env/.env
        """
        os_raw = (os.getenv("PY_ENV") or "").strip()
        if os_raw:
            return os_raw

        base_path = repo_root / "env" / ".env"
        if base_path.exists():
            vals = dotenv_values(str(base_path))  # read file only; don't export
            raw = (vals.get("PY_ENV") or vals.get("py_env") or "").strip() if vals else ""
            return raw or None

        return None

    # --- dotenv layering (files already handled separately) ---
    @staticmethod
    def _load_dotenv_layered(repo_root: Path, py_env: Optional[str]) -> None:
        """
        Load env/.env (no override), then env/<PY_ENV>.env (override=True).
        Real OS env remains the strongest source (python-dotenv default).
        """
        base = repo_root / "env" / ".env"
        if base.exists():
            load_dotenv(str(base), override=False)            # doesn't clobber OS env
        if py_env:
            overlay = repo_root / "env" / f"{py_env}.env"
            if overlay.exists():
                load_dotenv(str(overlay), override=True)      # overlay > base
        if py_env is not None:
            os.environ["PY_ENV"] = py_env                     # pin PY_ENV choice

    # --- discover TOML/YAML under env/ only ---
    @staticmethod
    def _config_files(repo_root: Path, py_env: Optional[str]) -> List[str]:
        """
        File merge order (low -> high):
          env/base.*  <  other env/*.{toml|yaml|yml} (alphabetical)  <  env/<PY_ENV>.*
        """
        env_dir = repo_root / "env"
        files: List[str] = []

        # 1) base.* lowest
        for name in ("base.toml", "base.yaml", "base.yml"):
            p = env_dir / name
            if p.exists():
                files.append(str(p))

        # 2) vendor/other files (middle), exclude base.* and <py_env>.*
        candidates = []
        for pat in ("*.toml", "*.yaml", "*.yml"):
            candidates.extend(env_dir.glob(pat))
        for p in sorted(candidates):
            n = p.name
            if n.startswith("base."):
                continue
            if py_env and n in {f"{py_env}.toml", f"{py_env}.yaml", f"{py_env}.yml"}:
                continue
            files.append(str(p))

        # 3) <py_env>.* highest among files
        if py_env:
            for name in (f"{py_env}.toml", f"{py_env}.yaml", f"{py_env}.yml"):
                p = env_dir / name
                if p.exists():
                    files.append(str(p))
        return files

    # --- public API ---
    #@lru_cache
    @staticmethod
    def load() -> ConfSetting:
        repo_root = ConfLoader._repo_root()
        py_env = ConfLoader._resolve_py_env(repo_root)

        # 1) Load/merge non-env config files first (lowest layer)
        config_files = ConfLoader._config_files(repo_root, py_env)

        # 2) Layer dotenv files (env/.env then env/<PY_ENV>.env) — OS env still highest
        ConfLoader._load_dotenv_layered(repo_root, py_env)

        # 3) Build settings. typed-settings merges files in order (last wins),
        #    then lets environment variables override file values.
        cfg = ts.load(
            cls=ConfSetting,
            appname="conf",                                 # required by your ts version
            config_files=config_files,
            env_prefix="",                                  # no prefix
            env_nested_delimiter="__",                      # GROUPA__URL -> groupa.url
        )
        # set the resolved py_env
        cfg.py_env = py_env

        return cfg
