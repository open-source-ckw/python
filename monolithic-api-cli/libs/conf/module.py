from nest.core import Module
from libs.conf.service import ConfService


@Module(
    controllers=[],
    providers=[ConfService],
    exports=[ConfService],
)
class ConfModule:
    pass
