from nest.core import Module

from libs.conf.module import ConfModule
from libs.log.module import LogModule
from libs.image_processing.service import ImageProcessingService


@Module(
    imports=[ConfModule, LogModule],
    controllers=[],
    providers=[ImageProcessingService],
    exports=[ImageProcessingService],
)
class ImageProcessingModule:
    pass
