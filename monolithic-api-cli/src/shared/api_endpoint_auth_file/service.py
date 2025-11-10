from typing import List
from nest.core import Injectable
from strawberry import Info
from libs.conf.service import ConfService
from libs.log.service import LogService
from libs.sql_alchemy.service import SqlAlchemyService
from libs.pynest_graphql import Context
from src.shared.api_endpoint_auth_file.factory import ApiEndpointAuthFileFactory


@Injectable
class ApiEndpointAuthFileService:
    def __init__(self, db: SqlAlchemyService, conf: ConfService, log: LogService, factory: ApiEndpointAuthFileFactory):
        self.db = db  # or db.use("main")
        self.conf = conf
        self.log = log
        self.factory = factory
        

    
