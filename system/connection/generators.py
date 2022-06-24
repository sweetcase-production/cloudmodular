from sqlalchemy.engine.base import Engine
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.orm.session import sessionmaker

from architecture.system.generator import (
    MariaDBGenerator, 
    MySQLGenerator,
    RDBGenerator, 
    SQLiteGenerator
)
from typing import Dict, Type


class DatabaseGenerator:

    db_map: Dict[str, Type[RDBGenerator]] = {
        'sqlite': SQLiteGenerator,
        'mariadb': MariaDBGenerator,
        'mysql': MySQLGenerator,
    }
    db: str = None


    @staticmethod
    def load(db_type: str, *args, **kwargs):
        DatabaseGenerator.db_map[db_type].init(*args, **kwargs)
        DatabaseGenerator.db = db_type
    
    @staticmethod
    def _get_gen():
        return DatabaseGenerator.db_map[DatabaseGenerator.db]

    @staticmethod
    def get_engine() -> Engine:
        return DatabaseGenerator._get_gen().get_engine()
    
    @staticmethod
    def get_base() -> DeclarativeMeta:
        return DatabaseGenerator._get_gen().get_base()
    
    @staticmethod
    def get_session() -> sessionmaker:
        return DatabaseGenerator._get_gen().get_session()


