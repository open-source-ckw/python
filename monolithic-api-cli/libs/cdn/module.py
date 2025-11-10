from nest.core import Module
from libs.libs_module import LibsModule
from libs.cdn.controller import CdnController
from libs.cdn.service import CdnService


@Module(
    imports=[LibsModule],
    controllers=[CdnController],
    providers=[CdnService],
    exports=[CdnService],
)
class CdnModule:
    pass
