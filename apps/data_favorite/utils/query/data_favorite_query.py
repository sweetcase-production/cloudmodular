from sqlalchemy import and_

from apps.storage.models import DataInfo
from architecture.query.crud import QueryCRUD, QueryUpdator
from core.exc import DataNotFound
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


class DataFavoriteQuery(QueryCRUD):
    updator = DataFavoriteQueryUpdator