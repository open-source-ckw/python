from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from nest.core import PyNestFactory
from nest.core.cli_factory import CLIAppFactory
from libs.conf.service import ConfService
from libs.conf.static import conf_static
from libs.jwt.http_guard import apply_jwt_guard_on_rest_endpoint
from libs.log.service import LogService
from libs.pynest_graphql.init import PyNestGraphQLInit
from libs.pynest_graphql.service import PyNestGraphQLService
from src.app_module import AppModule, AppCliModule
import uvicorn
import sys
from nest.core.pynest_application import PyNestApp
import asyncio

def boot(app):
    # method to add common process with every interface
    print("PyNest booting...")
    
    # Root@121
    # import psycopg2
    # connection = psycopg2.connect(
    #     host="103.251.16.205",   
    #     port="5434",                     
    #     database="ai_memory",
    #     user="admin",
    #     password="Root_121"
    # )
    # cursor = connection.cursor()
    # cursor.execute("SELECT version();")
    # print("===================")
    # print(cursor.fetchone())
    # print("===================")


# ██ API ██████████████████████████████████████████████████████

def boot_api():
    # create app, it will also add AppModule in DI container using container.add_module
    app: PyNestApp = PyNestFactory.create(
        AppModule,
        debug = True,
        lifespan = AppModule.lifespan
    )

    # get services from DI container
    conf = app.container.get_instance(ConfService)
    log = app.container.get_instance(LogService)
    #gql = app.container.get_instance(StrawberryGraphQLService)
    pyngql = app.container.get_instance(PyNestGraphQLService)
    plugin = app.container.get_instance(PyNestGraphQLInit)

    # Small runtime test: generate a thumbnail once at server startup.
    # print("=====IMAGEPROCESSING START ==============================")
    # from libs.image_processing.service import ImageProcessingService
    # pyvip = app.container.get_instance(ImageProcessingService)
    # try:
    #     img = asyncio.run(pyvip.generate_image_thumbnail(
    #         "/Users/core/Downloads/world-time.jpg",
    #         "/Users/core/Downloads/world-time-thumbnail.jpg",
    #         960, 600,
    #     ))
    #     print(img)
    # except Exception as e:
    #     # Don't crash the server if the test fails; just log it.
    #     print(f"IMAGEPROCESSING ERROR: {e}", file=sys.stderr)
    # finally:
    #     print("=====IMAGEPROCESSING END ==============================")

    # get FastAPI app
    http_server: FastAPI = app.get_server()

    # Registered a FastAPI ValueError exception handler so REST endpoints emit JSON error payloads 
    @http_server.exception_handler(ValueError)
    async def _handle_value_error(request: Request, exc: ValueError):
        message = str(exc).strip() or exc.__class__.__name__
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "errors": [
                    {
                        "message": message,
                        "extensions": {
                            "code": "BAD_USER_INPUT",
                            "type": exc.__class__.__name__,
                            "path": request.url.path,
                        },
                    }
                ]
            },
        )

    # set app metadata
    http_server.title = conf.app_name
    http_server.version = conf.app_version
    http_server.description = conf.project_name

    # Mount GraphQL under conf.graphql_root_slug with JWT auth
    #gql.mount(http_server, app=app)
    pyngql.mount(http_server, app=app, plugin=plugin)

    # apply JWT to REST api but exclude graphql as it will be handled separately
    slug_raw = getattr(conf, "gql_root_slug", None)
    slug = (str(slug_raw).strip() if slug_raw is not None else "") or "graphql"
    graphql_route = f"/{slug.strip('/')}"
    apply_jwt_guard_on_rest_endpoint(
        http_server,
        public_routes=[*conf.rest_public_routes, graphql_route],
    )

    boot(app)

    return http_server;

def start_api():
    # start server
    # if __name__ == "__main__":
    uvicorn.run(
        # boot_api(), # either: no hot reload
        "src.main:boot_api", # or: with hot reload
        reload=True, # (with hot reload only) if import string, not http_server object, for object no reload/workers
        
        host=conf_static.app_local_web_domain, 
        port=conf_static.app_local_web_port, 
        factory=True, 
        app_dir=".",
        log_level="info"
    )

def debug_api():
    import debugpy

    # Listen for a debugger; block until it attaches (optional)
    debugpy.listen((conf_static.debug_host, conf_static.debug_port))
    
    print(f"[debugpy] listening on {conf_static.debug_host}:{conf_static.debug_port}")
    print("[debugpy] waiting for client to attach…")
    print("Press F5 to attach debugger manually")
    debugpy.wait_for_client()
    print("[debugpy] client attached")

    # optional initial breakpoint but for REST not useful
    # try:
    #     debugpy.breakpoint()  # you can remove this if not needed
    # except Exception:
    #     pass

    # IMPORTANT: do NOT use reload here to avoid double-binding the port
    uvicorn.run(
        boot_api(),              # pass the app object (OK without reload/workers)
        host=conf_static.app_local_web_domain,
        port=conf_static.app_local_web_port,
    )


# ██ CLI ██████████████████████████████████████████████████████


def boot_cli():
    cli_app = CLIAppFactory().create(AppCliModule)
    
    boot(cli_app)
    return cli_app()
    

def start_cli():
    return boot_cli()

def debug_cli():
    import debugpy

    # start debug server once
    if not debugpy.is_client_connected():
        try:
            debugpy.listen((conf_static.debug_host, conf_static.debug_port))
            
            print(f"[debugpy] listening on {conf_static.debug_host}:{conf_static.debug_port}")
            print("[debugpy] waiting for client to attach…")
            print("Press F5 to attach debugger manually")
            debugpy.wait_for_client()
            print("[debugpy] client attached")
        except OSError as e:
            print(f"[debugpy] failed to listen: {e}", file=sys.stderr)

    # initial breakpoint at CLI entry:
    try:
        debugpy.breakpoint()  # you can remove this if not needed
    except Exception:
        pass

    return boot_cli()
