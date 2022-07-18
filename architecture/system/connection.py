from abc import ABCMeta, abstractmethod, ABC
from typing import Any, Dict

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.engine.base import Engine
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.orm.session import sessionmaker as class_sessionmaker

class InfraConnection(metaclass=ABCMeta):
    """
    서비스 및 인프라 커넥션
    """
    __infras__: Dict[str, Dict[str, Any]] = dict()

    def __new__(cls, *args, **kwargs):
        """
        Infra Connection은 단 하나의 인스턴스만 생성되어야 한다.
        """
        instance_name = cls.__name__    # Class Name
        if not instance_name in InfraConnection.__infras__:
            # 처음 할당하는 경우
            record = {
                'instance': super(InfraConnection, cls).__new__(cls),
                'loaded': False,    # 처음 생성할 때 사용
            }
            InfraConnection.__infras__[instance_name] = record
        instance = InfraConnection.__infras__[instance_name]['instance']
        return instance

    def __init__(self, *args, **kwargs):
        class_name = type(self).__name__
        if not InfraConnection.__infras__[class_name]['loaded']:
            """
            처음 인스턴스가 새로 생성된 경우다
            이때는 멤버 변수 자체가 초기화가 안되어 있기 때문에
            _load 함수로 전부 초기화 한다.
            반대의 경우 이미 되어 있기 때문에 할 필요가 없다.
            """
            InfraConnection.__infras__[class_name]['loaded'] = True
            self._load(*args, **kwargs)

    @abstractmethod
    def _load(self, *args, **kwargs):
        """
        멤버 변수 초기화 함수
        """
        pass

    @classmethod
    def get_instance(cls):
        """
        보통 여기로 인스턴스를 받는다.
        """
        try:
            instance_record = InfraConnection.__infras__[cls.__name__]
            if not instance_record['loaded']:
                raise RuntimeError()
        except Exception:
            raise RuntimeError('Init Connection First')
        else:
            return InfraConnection.__infras__[cls.__name__]['instance']

    def reload(self, *args, **kwargs):
        """
        인스턴스 강제 reload
        """
        self._load(*args, **kwargs)


class RDBConnection(InfraConnection, ABC):
    """
    관계형 데이터베이스 커넥션
    sqlalchemy 엔진을 사용한다.
    """
    
    engine: Engine
    base: DeclarativeMeta
    session: class_sessionmaker
    url: str

    @abstractmethod
    def _load(self, *args, **kwargs):
        """
        DB Engine Load Function
        """
        pass

    @property
    def Engine(self) -> Engine:
        return self.engine
    
    @property
    def ModelBase(self) -> DeclarativeMeta:
        return self.base
    
    @property
    def Session(self) -> class_sessionmaker:
        return self.session()

class ProgramedRDBConnection(RDBConnection, ABC):
    """
    MySQL, MariaDB, PostrgreSQL ETC...
    """
    config: Dict[str, Any]
    host: str
    port: int
    database: str
    user: str
    passwd: str
    database_type: str

    def _load(
        self,
        database_type: str,
        host: str,
        port: int,
        database: str,
        user: str,
        passwd: str,
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.passwd = passwd
        self.database_type = database_type

        self.url = \
            f'{database_type}://{user}:{passwd}@{host}:{port}/{database}'
        
        self.engine = create_engine(self.url)
        self.session = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        self.base = declarative_base()

class MySQLConnection(ProgramedRDBConnection):
    def _load(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        passwd: str
    ):
        super()._load(
            database_type='mysql',
            host=host,
            port=port,
            database=database,
            user=user,
            passwd=passwd,
        )

class MariaDBConnection(ProgramedRDBConnection):
    def _load(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        passwd: str
    ):
        super()._load(
            database_type='mariadb',
            host=host,
            port=port,
            database=database,
            user=user,
            passwd=passwd,
        )

class SQLiteConnection(RDBConnection):
    def _load(self):
        self.url = 'sqlite:///data.db?check_same_thread=False'
        self.engine = create_engine(self.url)
        self.session = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        self.base = declarative_base()
