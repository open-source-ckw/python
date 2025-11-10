
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from nest.core import Module
from libs.cdn.module import CdnModule
from libs.libs_module import LibsModule
from src.app_service import AppService
from src.app_controller import AppController
from src.app_cli import AppCli
from src.shared.shared_module import SharedCliModule, SharedModule
from src.business.business_module import BusinessCliModule, BusinessModule
from src.ai.ai_module import AiCliModule, AiModule
from src.third_party.third_party_module import ThirdPartyCliModule, ThirdPartyModule
from libs.strawberry_graphql.module import StrawberryGraphQLModule
from libs.cdn.module import CdnModule
from libs.pynest_graphql.module import PyNestGraphQLModule
@Module(
    imports=[
        CdnModule,
        LibsModule, 

        # do not import in libs as its not required everywhere
        #StrawberryGraphQLModule,
        PyNestGraphQLModule,

        AiModule, 
        SharedModule, 
        BusinessModule, 
        ThirdPartyModule,
        CdnModule,
    ],
    controllers=[AppController],
    providers=[AppService],
    exports=[],
)
class AppModule:
    """
    Do not create def __init__ 
    this break the app on shutdown in addtion might not be suitable as per envirinment of the app
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # this is ONLY for the api app NOT for cli app
        # task to perform on application startup
        # apply only process which is related with api app only and not cli
        # if any operation required both find alternative solution do not use boot patchup here
        print("lifespan: Attached to application...")

        try:
            print("lifespan: Application starting up...")
            
            yield
        except asyncio.CancelledError:
            # Swallow SIGINT cancellation during shutdown
            pass
        finally:
            # Task to perform on application shutdown
            print("lifespan: Application shutting down...")

@Module(
    imports=[
        LibsModule,
        AiCliModule,
        SharedCliModule,
        BusinessCliModule,
        ThirdPartyCliModule
    ],
    controllers=[AppCli],
    providers=[AppService],
    exports=[],
)
class AppCliModule:
    """
    REQUIRED 2 Modules to maange REST and CLI app

    The API boot path expects HTTP controllers only.
    When Uvicorn starts, PyNest’s RouteResolver iterates module.controllers and calls get_router() on each.
    @CliController() doesn’t have get_router(), so it gives error and app do not start
    """

    pass
