from sqlalchemy import and_, func
from typing import Optional, Sequence

from apps.storage.models import DataInfo
from apps.storage.schemas import DataInfoCreate
from architecture.query.crud import (
    QueryCRUD,
    QueryCreator,
    QueryDestroyer,
    QueryReader,
    QueryUpdator,
)
from core.exc import DataAlreadyExists, DataNotFound
from system.connection.generators import DatabaseGenerator

class DataDBQueryCreator(QueryCreator):
    def __call__(self, data_format: DataInfoCreate) -> DataInfo:

        session = DatabaseGenerator.get_session()
        q = session.query(DataInfo)

        data: DataInfo = DataInfo(
            name=data_format.name,
            root=data_format.root,
            user_id=data_format.user_id,
            is_dir=data_format.is_dir,
        )
        # user_id & name & root & is_dir일 경우 생성 불가능
        if q.filter(and_(
            DataInfo.name == data.name,
            DataInfo.root == data.root,
            DataInfo.user_id == data.user_id,
            DataInfo.is_dir == data.is_dir
        )).scalar():
            raise DataAlreadyExists()
        
        try:
            # DB 업로드
            session.add(data)
            session.commit()
            session.refresh(data)
        except Exception as e:
            session.rollback()
            raise e
        else:
            return data
        finally:
            session.close()

class DataDBQueryDestroyer(QueryDestroyer):
    def __call__(self, data_id: int) -> Optional[DataInfo]:
        session = DatabaseGenerator.get_session()
        q = session.query(DataInfo)
        
        data: DataInfo = q.filter(DataInfo.id == data_id).scalar()
        try:
            if not data.is_dir:
                # 파일
                q.filter(DataInfo.id == data_id).delete()
            else:
                # 디렉토리
                # 하위 데이터 전부 삭제
                q.filter(and_(
                    DataInfo.user_id == data.user_id,
                    DataInfo.root.startswith(f'{data.root}{data.name}/')
                )).delete(synchronize_session='fetch')
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        else:
            return data
        finally:
            session.close()

class DataDBQueryReader(QueryReader):
    def __call__(
        self, user_id: int,
        is_dir: Optional[bool] = None,
        data_id: Optional[int] = None,
        full_root: Optional[Sequence[str]] = None
    ) -> DataInfo:
        session = DatabaseGenerator.get_session()
        q = session.query(DataInfo)

        try:
            if data_id:
                # search by data_id
                data: DataInfo = q.filter(and_(
                    DataInfo.user_id == user_id,
                    DataInfo.id == data_id,
                )).scalar()
            elif full_root:
                data: DataInfo = q.filter(and_(
                    DataInfo.user_id == user_id,
                    DataInfo.root == full_root[0],
                    DataInfo.name == full_root[1],
                )).scalar()
        except Exception as e:
            session.rollback()
            raise e
        else:
            if is_dir:
                if data and data.is_dir != is_dir:
                    return None
            return data
        finally:
            session.close()

class DataDBQueryUpdator(QueryUpdator):
    def __call__(
        self, new_name: str,
        data_info: Optional[DataInfo] = None,
        user_id: Optional[int] = None,
        data_id: Optional[int] = None,
    ) -> DataInfo:
        session = DatabaseGenerator.get_session()
        q = session.query(DataInfo)
        if not data_info:
            # 아이디로 찾는 경우
            data_info = q.filter(and_(
                DataInfo.user_id == user_id,
                DataInfo.data_id == data_id,
            )).scalar()
        if not data_info:
            # 그래도 못찾음
            raise DataNotFound()
        try:
            # 파일의 이름 수정
            prev_name = data_info.name
            data_info.name = new_name
            if data_info.is_dir:
                # 디렉토리인 경우 하위 디렉토리의 루트 수정
                """
                TODO 리펙토링 진행 시 어차피 DB 테이블 재설계할거라
                동작되는 정도만
                """
                dst_root = data_info.root + prev_name + '/'
                src_root = data_info.root + new_name + '/'
                targets = q.filter(and_(
                    DataInfo.user_id == user_id,
                    DataInfo.root.startswith(dst_root),
                )).all()
                for target in targets:
                    target.root = target.root.replace(dst_root, src_root)
            session.commit()
            session.refresh(data_info)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            return data_info

class DataDBQuery(QueryCRUD):
    creator = DataDBQueryCreator
    destroyer = DataDBQueryDestroyer
    reader = DataDBQueryReader
    updator = DataDBQueryUpdator