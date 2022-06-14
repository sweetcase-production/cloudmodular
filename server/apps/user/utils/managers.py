from typing import Optional
from apps.user.models import User
from apps.user.schemas import UserCreate
from apps.user.utils.queries.user_db_query import UserDBQuery
from apps.user.utils.queries.user_storage_query import UserStorageCreator, UserStorageQuery
from architecture.manager.backend_manager import CRUDManager


class UserCRUDManager(CRUDManager):


    def create(
        email: str,
        name: str,
        passwd: str,
        storage_size: str,
        is_admin: bool = False,
    ):
        # DB Upload
        user_schema = UserCreate(
            email=email,
            name=name,
            passwd=passwd,
            storage_size=storage_size,
            is_admin=is_admin
        )
        user: User = UserDBQuery().create(user_schema)
        # Directory 생성
        try:
            UserStorageCreator().create(user_id=user.id, force=True)
        except Exception as e:
            # 실패시 User 삭제
            UserDBQuery().destroy(user_id=user.id)
            raise e

    def update():
        raise NotImplementedError
    
    def read():
        raise NotImplementedError

    def destroy(
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        user_id: Optional[int] = None
    ):
        removed_id = UserDBQuery().destroy(
            user_name=user_name,
            user_email=user_email,
            user_id=user_id
        )
        UserStorageQuery().destory(user_id=removed_id)
    def search():
        raise NotImplementedError