from sqlalchemy import and_, or_
from sqlalchemy.sql import func
from typing import Dict, List, Optional
import bcrypt

from apps.user.models import User
from apps.data_tag.models import DataTag
from apps.storage.models import DataInfo
from apps.tag.models import Tag
from apps.user.schemas import UserCreate, UserUpdate
from architecture.query.crud import (
    QueryCRUD, 
    QueryCreator, 
    QueryDestroyer, 
    QueryReader,
    QuerySearcher,
    QueryUpdator
)
from core.exc import UserAlreadyExists, UserNotFound
from system.connection.generators import DatabaseGenerator



class UserDBQueryCreator(QueryCreator):
    def __call__(self, user_format: UserCreate) -> User:

        session = DatabaseGenerator.get_session()
        q = session.query(User)
        # 동일한 name이나 email이 있으면 안된다.
        if q.filter(or_(
                    User.name == user_format.name, 
                    User.email == user_format.email
                )).scalar():
                raise UserAlreadyExists()
        if user_format.is_admin and q.filter(User.is_admin == True).scalar():
            # admin은 단 하나만 생성할 수 있다.
            raise PermissionError()
        try:
            # DB 저장

            # Serializer -> Dict
            request = user_format.dict()
            # 패스워드 암호화
            request['passwd'] = \
                bcrypt.hashpw(
                    request['passwd'].encode('utf-8'),
                    bcrypt.gensalt())
            # DB 업로드
            user: User = User(**request)
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

class UserDBQueryUpdator(QueryUpdator):
    def __call__(self, update_format: UserUpdate) -> User:

        session = DatabaseGenerator.get_session()
        q = session.query(User)
        # 해당 유저가 존재하는 지 확인한다.
        user: User = q.filter(User.id == update_format.id).scalar()
        if not user:
            # 유저 없음
            raise UserNotFound()
        # 데이터 변경 시도
        user.name = update_format.name
        if update_format.passwd != '':
            # 암호화 해서 저장
            user.passwd = bcrypt.hashpw(
                update_format.passwd.encode('utf-8'),
                bcrypt.gensalt())
        # 커밋
        try:
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
        user_id: Optional[int] = None,
        is_admin: Optional[bool] = False,
    ) -> Optional[User]:

        session = DatabaseGenerator.get_session()
        q = session.query(User)
        user: User = None
        try:
            if is_admin:
                user = q.filter(User.is_admin == True).scalar()
            elif user_name:
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
            if user:

                # Data 관련 Tag 제거
                data_infos = session.query(DataInfo, DataTag, Tag).filter(and_(
                    DataInfo.id == user.id,
                    DataTag.datainfo_id == DataInfo.id,
                    Tag.id == DataTag.tag_id,
                )).all()
                for _, _, tag in data_infos:
                    session.delete(tag)
                session.delete(user)
                session.commit()
            else:
                # 삭제 대상의 유저가 없는 경우
                raise UserNotFound()
        except Exception as e:
            session.rollback()
            raise e
        else:
            return user.id
        finally:
            session.close()

class UserDBQuerySearcher(QuerySearcher):
    def __call__(self, page: int, page_size: int):
        start = page_size * (page - 1)
        session = DatabaseGenerator.get_session()
        q = session.query(User)
        try:
            users: List[User] = \
                q.order_by(User.created.asc()) \
                    .offset(start).limit(page_size).all()
        except Exception as e:
            raise e
        else:
            return users
        finally:
            session.close()

class UserDBQuery(QueryCRUD):
    reader = UserDBQueryReader
    creator = UserDBQueryCreator
    destroyer = UserDBQueryDestroyer
    updator = UserDBQueryUpdator
    searcher = UserDBQuerySearcher

    def read_usage(self, user_id: int) -> Dict[str, int]:
        # 사용량 구하기
        session = DatabaseGenerator.get_session()
        # Check User Data
        user: User = \
            session.query(User) \
                .filter(User.id == user_id).scalar()
        if not user:
            raise UserNotFound()
        entire = user.storage_size * (10 ** 9) # GB -> Byte
        # Check Usage size
        used = session.query(func.sum(DataInfo.size)) \
            .filter(DataInfo.user_id == user_id) \
            .group_by(DataInfo.user_id).scalar()
        return {
            'entire': entire,
            'used': used if used else 0
        }