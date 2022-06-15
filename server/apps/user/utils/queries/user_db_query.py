from sqlalchemy import or_
from typing import Optional

from apps.user.models import User
from apps.user.schemas import UserCreate
from architecture.query.crud import (
    QueryCRUD, 
    QueryCreator, 
    QueryDestroyer, 
    QueryReader
)
from system.connection.generators import DatabaseGenerator



class UserDBQueryCreator(QueryCreator):
    def __call__(self, user_format: UserCreate) -> User:

        session = DatabaseGenerator.get_session()
        q = session.query(User)
        # 동일한 name이나 email이 있으면 안된다.
        assert q.filter(or_(
                    User.name == user_format.name, 
                    User.email == user_format.email
                )).scalar() is None
        if user_format.is_admin:
            # admin은 단 하나만 생성할 수 있다.
            assert q.filter(User.is_admin == True).scalar() is None
        try:
            # DB 업로드
            user: User = User(**(user_format.dict()))
            session.add(user)
            session.commit()
            session.refresh(user)
        except Exception as e:
            # 실패 시 rollback
            session.rollback()
            raise e
        else:
            return user
        finally:
            session.close()

class UserDBQueryReader(QueryReader):
    def __call__(
        self,
        user_name: Optional[str] = None, 
        user_email: Optional[str] = None, 
        user_id: Optional[int] = None
    ) -> Optional[User]:

        session = DatabaseGenerator.get_session()
        q = session.query(User)
        user: User = None

        try:
            if user_name:
                user = q.filter(User.name == user_name).scalar()
            elif user_email:
                user = q.filter(User.email == user_email).scalar()
            elif user_id:
                user = q.filter(User.id == user_id).scalar()
        except Exception as e:
            session.rollback()
            raise e
        else:
            return user
        finally:
            session.close()


class UserDBQueryDestroyer(QueryDestroyer):
    def __call__(
        self,
        user_name: Optional[str] = None, 
        user_email: Optional[str] = None, 
        user_id: Optional[int] = None
    ) -> int:

        session = DatabaseGenerator.get_session()
        q = session.query(User)
        user: User = None
        try:
            if user_name:
                user = q.filter(User.name == user_name).scalar()
            if user_email:
                user = q.filter(User.email == user_email).scalar()
            if user_id:
                user = q.filter(User.id == user_id).scalar()    
            # 모든 DB데이터 삭제
            q.filter(user.id == user.id).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        else:
            return user.id
        finally:
            session.close()

class UserDBQuery(QueryCRUD):
    reader = UserDBQueryReader()
    creator = UserDBQueryCreator()
    destroyer = UserDBQueryDestroyer()