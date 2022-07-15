import os
import shutil

from settings.base import SERVER, DATABASE
from system.connection.generators import DatabaseGenerator


class Bootloader:

    """
    시스템 실행 시 기본적인 세팅을 담당한다.
    Pytest애서도 쓰인다.

    Directory Setting
    cloudmodular
        user1
            storage
        user2...
    """

    @staticmethod
    def init_storage():
        """
        초기 디렉토리 생성
        cloudmodular라는 디렉토리를 생성한다.
        """
        if not os.path.isdir(os.getenv('SERVER_STORAGE')):
            raise FileNotFoundError('Main Directory Not Found')
        root = SERVER['storage']
        if not os.path.isdir(root):
            os.mkdir(root)
        # 사용자 개인 데이터 저장에 사용되는 storage 디렉토리 생성
        os.mkdir(f'{root}/storage')

    @staticmethod
    def remove_storage():
        """
        모든 스토리지들을 삭제한다.
        """
        shutil.rmtree(SERVER['storage'])

    @staticmethod
    def migrate_database():
        """
        데이터베이스 마이그레이트
        """
        
        # 생성 할 테이블 Import
        from apps.user.models import User
        from apps.storage.models import DataInfo
        from apps.tag.models import Tag
        from apps.data_tag.models import DataTag

        Base = DatabaseGenerator.get_base()
        db_engine = DatabaseGenerator.get_engine()
        Base.metadata.create_all(db_engine)

    @staticmethod
    def remove_database():
        """
        데이터베이스 초기화
        """
        if DATABASE['type'] == 'sqlite':
            """
            SQLITE일 경우 자체 삭제
            """
            os.remove('data.db')
        else:
            from apps.user.models import User
            from apps.storage.models import DataInfo
            from apps.tag.models import Tag
            from apps.data_tag.models import DataTag
            
            session = DatabaseGenerator.get_session()
            session.query(DataTag).filter(DataTag.id >= 0).delete()
            session.query(Tag).filter(Tag.id >= 0).delete()
            session.query(DataInfo).filter(DataInfo.id >= 0).delete()
            session.query(User).filter(User.id >= 0).delete()
            session.commit()
