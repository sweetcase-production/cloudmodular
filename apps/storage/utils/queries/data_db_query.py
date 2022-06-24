from sqlalchemy import and_
from typing import Optional, Sequence

from apps.storage.models import DataInfo
from apps.storage.schemas import DataInfoCreate
from architecture.query.crud import (
    QueryCRUD,
    QueryCreator,
    QueryDestroyer,
    QueryReader,
)
from core.exc import DataAlreadyExists
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
            q.filter(DataInfo.id == data_id).delete()
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
        is_dir: bool,
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
            if data and data.is_dir != is_dir:
                return None
            else:
                return data
        finally:
            session.close()

class DataDBQuery(QueryCRUD):
    creator = DataDBQueryCreator
    destroyer = DataDBQueryDestroyer
    reader = DataDBQueryReader