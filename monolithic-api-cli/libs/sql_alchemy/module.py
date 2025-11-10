# libs/sql_alchemy/module.py

from nest.core import Module

from libs.sql_alchemy.service import SqlAlchemyService


@Module(
    imports=[],
    providers=[SqlAlchemyService],
    exports=[SqlAlchemyService],
)
class SqlAlchemyModule:
    pass
