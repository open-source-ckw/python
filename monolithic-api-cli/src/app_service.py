from nest.core import Injectable
import click
from libs.conf.service import ConfService
from libs.libs_service import LibsService
from libs.log.service import LogService

@Injectable
class AppService:
    def __init__(self, conf: ConfService, log: LogService, libs: LibsService):
        self.conf = conf
        self.log = log
        self.libs = libs

        self.app_name = "ai-thatsend-work-api"
        self.app_version = "0.1.0"

    def get_app_info(self):
        msg = "from hello to module"
        conf = self.conf.app_name
        # self.conf.debug("info FROM cli PyNest app!", msg=msg, conf=conf)
        return {"app_name": f"{self.app_name} - {msg} - {conf}", "app_version": self.app_version} 
    
    async def version(self):
        print(click.style("1.0.0", fg="blue"))
        
    async def info(self):
        msg = "from hello to module"
        conf = self.conf.app_name
        #self.conf.notice("info FROM cli PyNest app!", msg=msg, conf=conf)
        print(click.style(f"This is a cli nest app! > {msg} > {conf}", fg="green"))

        