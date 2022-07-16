from datetime import datetime
from typing import Optional

from sqlalchemy import and_
from apps.share.models import DataShared
from apps.storage.models import DataInfo
from architecture.query.crud import QueryCRUD, QueryCreator, QueryReader, QueryUpdator
from system.connection.generators import DatabaseGenerator

class DataSharedQueryCreator(QueryCreator):
    def __call__(self, data_id: int):
        session = DatabaseGenerator.get_session()
        # Search
        shared = session.query(DataShared) \
            .filter(DataShared.datainfo_id == data_id).scalar()
        if shared:
            raise ValueError('This shared data already exists')
        # add
        shared = DataShared(datainfo_id=data_id)
        try:
            session.add(shared)
            session.commit()
            session.refresh(shared)
        except Exception as e:
            session.rollback()
            raise e
        else:
            return shared

class DataSharedQueryUpdator(QueryUpdator):
    def __call__(self, shared_id: int, is_active: bool):
        session = DatabaseGenerator.get_session()
        # search
        shared = session.query(DataShared) \
            .filter(DataShared.id == shared_id).scalar()
        if not shared:
            raise ValueError('This shared data is not exists')
        # update
        shared.is_active = is_active
        if is_active:
            # 재공유시 현재 시간으로 초기화
            shared.share_started = datetime.now()
        try:
            session.commit()
            session.refresh(shared)
        except Exception as e:
            session.rollback()
            raise e
        else:
            return shared

class DataSharedQueryReader(QueryReader):
    def __call__(
        self, 
        shared_id: Optional[int] = None,
        data_id: Optional[int] = None, user_id: Optional[int] = None,
    ):
        session = DatabaseGenerator.get_session()
        # search
        if shared_id:
            shared = session.query(DataShared) \
                .filter(DataShared.id == shared_id).scalar()
            return shared
        elif data_id and user_id:
            shared = session.query(DataInfo, DataShared) \
                .filter(and_(
                    DataInfo.user_id == user_id,
                    DataInfo.id == data_id,
                    DataShared.datainfo_id == DataInfo.id,
                )).first()
            return None if not shared else shared[1]

class DataSharedQuery(QueryCRUD):
    creator = DataSharedQueryCreator
    updator = DataSharedQueryUpdator
    reader = DataSharedQueryReader