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
    def get_engine():
        return DatabaseGenerator._get_gen().get_engine()
    
    @staticmethod
    def get_base():
        return DatabaseGenerator._get_gen().get_base()
    
    @staticmethod
    def get_session():
        return DatabaseGenerator._get_gen().get_session()


