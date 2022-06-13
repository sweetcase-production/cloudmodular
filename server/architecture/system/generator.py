from abc import ABCMeta, ABC
from typing import Type
from architecture.system.connection import InfraConnection, MariaDBConnection, MySQLConnection, RDBConnection, SQLiteConnection



class InfraGenerator(metaclass=ABCMeta):
    """
    인프라 인스턴스 제너레이터
    Connection을 사용하지 않고 이 클래스를 통해 인스턴스를 받는다.
    """
    conn: Type[InfraConnection]

    @classmethod
    def init(cls, *args, **kwargs):
        # 인스턴스 초기화
        cls.conn(*args, **kwargs)


class RDBGenerator(InfraGenerator, ABC):
    """
    RDB 전용 인스턴스 생성기
    """
    conn: Type[RDBConnection]

    @classmethod
    def get_engine(cls):
        return cls.conn.get_instance().Engine

    @classmethod
    def get_base(cls):
        return cls.conn.get_instance().ModelBase
    
    @classmethod
    def get_session(cls):
        return cls.conn.get_instance().Session

class MySQLGenerator(RDBGenerator):
    conn = MySQLConnection

class MariaDBGenerator(RDBGenerator):
    conn = MariaDBConnection

class SQLiteGenerator(RDBGenerator):
    conn = SQLiteConnection