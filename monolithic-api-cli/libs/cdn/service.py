# libs/conf/conf_service.py
from typing import Any, Optional
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse
from nest.core import Injectable

from libs.conf.service import ConfService
from libs.log.service import LogService


# Note: keep parameter types simple (str) to avoid UnionType issues in runtime defaults.


@Injectable
class CdnService:
    """Small helper to build CDN URLs for tmp, image, and upload roots.

    Centralizes how URLs are composed so only this service (and the CDN
    controller) needs changes if paths or structure evolve.
    """

    def __init__(self, conf: ConfService, log: LogService) -> None:
        self.conf = conf
        self.log = log
        self.log.bind(service=self.__class__.__name__)

    # ---- public API ----------------------------------------------------
    def getTmpCdnUrl(self, path: Optional[str] = None, *, absolute: bool = True) -> str:
        """Return URL under /cdn/t for tmp assets.

        Example: /cdn/t/foo/bar.txt  (or absolute with domain)
        """
        rel = self._compose_url(self._cdn_root(), "t", self._to_str_path(path))
        return self._compose_url(self._cdn_domain(), rel) if absolute else rel

    def getImageCdnUrl(self, path: Optional[str] = None, *, absolute: bool = True) -> str:
        """Return URL under /cdn/i for image assets.

        Example: /cdn/i/icons/file.svg  (or absolute with domain)
        """
        rel = self._compose_url(self._cdn_root(), "i", self._to_str_path(path))
        return self._compose_url(self._cdn_domain(), rel) if absolute else rel

    def getUploadCdnUrl(self, path: Optional[str] = None, *, absolute: bool = True) -> str:
        """Return URL under /cdn/u for uploaded assets.

        Example: /cdn/u/api_endpoint_auth/1/file.jpg  (or absolute with domain)
        """
        rel = self._compose_url(self._cdn_root(), "u", self._to_str_path(path))
        return self._compose_url(self._cdn_domain(), rel) if absolute else rel

    def getDefaultAudioIcon(self, *, absolute: bool = True) -> str:
        """Return default audio thumbnail/icon URL."""
        return self.getImageCdnUrl("file-icons/audio.svg", absolute=absolute)

    def getDefaultVideoIcon(self, *, absolute: bool = True) -> str:
        """Return default video thumbnail/icon URL."""
        return self.getImageCdnUrl("file-icons/video.svg", absolute=absolute)

    def getDefaultFileIcon(self, *, absolute: bool = True) -> str:
        """Return default generic file thumbnail/icon URL."""
        return self.getImageCdnUrl("file-icons/file.svg", absolute=absolute)

    # ---- internals -----------------------------------------------------
    def _compose_url(self, base: str, *parts: str) -> str:
        base = base.rstrip("/") + "/"
        path = "/".join(p.strip("/") for p in parts if p is not None and str(p) != "")
        return base + path

    def _cdn_domain(self) -> str:
        # Prefer dedicated CDN domain, fallback to app host domain
        return getattr(self.conf, "app_host_cdn_domin", None) or self.conf.app_host_domain

    def _cdn_root(self) -> str:
        # Mount point for CDN routes (e.g., "/cdn")
        return getattr(self.conf, "cdn_url", "/cdn")

    def _to_str_path(self, path: Optional[str]) -> str:
        if path is None:
            return ""
        return str(path)
    
    # ---- static file serving (used by controller) ----------------------
    def _serve_from(self, base: Path, rel_path: str) -> FileResponse:
        """Safely serve a file from a base directory.

        Ensures `rel_path` remains within `base`, and sets long-lived cache headers.
        """
        root = Path(self.conf.root_path).resolve()
        base_path = base if base.is_absolute() else (root / base).resolve()
        target = (base_path / (rel_path or "").lstrip("/")).resolve()

        try:
            _ = target.relative_to(base_path)
        except Exception:
            raise HTTPException(status_code=404, detail="File not found")

        if not target.exists() or not target.is_file():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            str(target),
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
            },
        )

    def serve_tmp(self, rel_path: str) -> FileResponse:
        return self._serve_from(self.conf.tmp_dir_path, rel_path)

    def serve_image(self, rel_path: str) -> FileResponse:
        return self._serve_from(self.conf.image_dir_path, rel_path)

    def serve_upload(self, rel_path: str) -> FileResponse:
        return self._serve_from(self.conf.upload_dir_path, rel_path)
