import asyncio
from pathlib import Path
from typing import Optional

from nest.core import Injectable

from libs.conf.service import ConfService
from libs.log.service import LogService

import pyvips


@Injectable
class ImageProcessingService:
    """Service that mirrors the NestJS image processing helper using pyvips."""

    def __init__(self, conf: ConfService, log: LogService) -> None:
        self.conf = conf
        self.log = log
        
        self.log.bind(context=ImageProcessingService.__name__)

    async def generate_image_thumbnail(
        self,
        input_image_path: str,
        output_thumbnail_path: str,
        width: int,
        height: int,
    ) -> str:
        """Create an entropy-cropped thumbnail asynchronously."""

        source = Path(input_image_path)
        target = Path(output_thumbnail_path)
        kwargs = self._entropy_crop_kwargs()

        def _process() -> str:
            image = pyvips.Image.thumbnail(
                str(source),
                width,
                height=height,
                **kwargs,
            )
            image.write_to_file(str(target))
            return str(target)

        try:
            result = await asyncio.to_thread(_process)
        except Exception as error:  # pragma: no cover - runtime failure path
            self.log.error("Error generating thumbnail", error=str(error))
            raise RuntimeError("Error generating thumbnail") from error

        self.log.info(f"Thumbnail created: {target}")
        return result

    def _entropy_crop_kwargs(self) -> dict[str, object]:
        """Resolve kwargs for entropy-based cropping compatible across pyvips versions.

        Some pyvips/libvips versions do not accept the "interesting" kwarg on
        Image.thumbnail(). Instead, pass the entropy mode via the "crop" option.
        """
        kwargs: dict[str, object] = {}

        # Prefer enum if available; otherwise fall back to string value.
        interesting: Optional[object] = None
        for attr in ("Interesting", "interesting"):
            interesting = getattr(pyvips, attr, None)
            if interesting is not None:
                break

        if interesting is not None:
            entropy = getattr(interesting, "ENTROPY", None)
            if entropy is not None:
                kwargs["crop"] = entropy  # enum value
                return kwargs

        # Fallback works on older/newer pyvips: pass string name
        kwargs["crop"] = "entropy"
        return kwargs
