from nest.core import Module

from libs.conf.module import ConfModule
from libs.log.configuration import LogConfiguration
from libs.log.service import LogService


@Module(
    imports=[ConfModule],
    controllers=[],
    providers=[LogService],
    exports=[LogService],
)
class LogModule:
    pass
