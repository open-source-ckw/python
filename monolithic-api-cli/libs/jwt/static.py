from typing import Final
from libs.conf.static import conf_static
from libs.log.static import log_static
from libs.jwt.service import JwtService
from libs.jwt.guard import JwtGuard

jwt_static: Final = JwtService(conf_static, log_static)
jwt_guard_static: Final = JwtGuard(conf_static, log_static, jwt_static)