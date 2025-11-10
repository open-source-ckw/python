# libs/jwt/module.py
from nest.core import Module
from libs.jwt.service import JwtService
from libs.jwt.guard import JwtGuard
from libs.jwt.utils import JwtUtils
from libs.jwt.keystore import JwtKeyStore
from libs.jwt.revocation_store import JwtRevocationStore

@Module(
    imports=[],
    controllers=[],
    providers=[JwtService, JwtGuard],
    exports=[JwtService, JwtGuard],
)
class JwtModule:
    # DI module only; no business logic
    pass
