from nest.core import Module

from libs.conf.module import ConfModule
from libs.jwt.module import JwtModule
from libs.log.module import LogModule
from libs.libs_service import LibsService
from libs.sql_alchemy.module import SqlAlchemyModule
from libs.template_engine.module import TemplateEngineModule
    
@Module(
    is_global=True,
    imports=[
        ConfModule,
        LogModule,
        SqlAlchemyModule,
        JwtModule,
        TemplateEngineModule
    ],
    controllers=[],
    providers=[LibsService],
    exports=[
        LibsService,
        
        ConfModule,
        LogModule,
        SqlAlchemyModule,
        JwtModule,
        TemplateEngineModule,
    ],
)
class LibsModule:
    pass
