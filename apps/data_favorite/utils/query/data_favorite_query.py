from typing import List
from sqlalchemy import and_

from apps.storage.models import DataInfo
from architecture.query.crud import QueryCRUD, QuerySearcher, QueryUpdator
from core.exc import DataNotFound, IsNotDirectory
from system.connection.generators import DatabaseGenerator

class DataFavoriteQueryUpdator(QueryUpdator):
    # Favorite On/OFF
    def __call__(self, user_id: int, data_id: int, is_favorite: bool):
        session = DatabaseGenerator.get_session()
        data_info: DataInfo = \
            session.query(DataInfo).filter(and_(
                DataInfo.user_id == user_id,
                DataInfo.id == data_id,
            )).scalar()
        if not data_info:
            raise DataNotFound()
        if data_info.is_favorite == is_favorite:
            raise ValueError()
        data_info.is_favorite = is_favorite
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

class DataFavoriteQuerySearcher(QuerySearcher):

    def __call__(self, user_id: int, data_id: int) -> List[DataInfo]:
        session = DatabaseGenerator.get_session()
        data_info: DataInfo = \
            session.query(DataInfo).filter(and_(
                DataInfo.user_id == user_id,
                DataInfo.id == data_id,
            )).scalar()
        if data_id != 0 and not data_info:
            raise DataNotFound()
        if data_id != 0 and not data_info.is_dir:
            raise IsNotDirectory()
        
        # 루트 디렉토리 생ㅅ어
        if data_id != 0:
            directory_root = f'{data_info.root}{data_info.name}/'
        else:
            # data_id == 0 -> 최상위 루트
            directory_root = '/'
        
        # 쿼리
        return session.query(DataInfo).filter(and_(
            DataInfo.user_id == user_id,
            DataInfo.root == directory_root,
            DataInfo.is_favorite == True,
        )).all()

class DataFavoriteQuery(QueryCRUD):
    updator = DataFavoriteQueryUpdator
    searcher = DataFavoriteQuerySearcher