from typing import Optional

from apps.user.models import User
from apps.user.schemas import UserCreate
from apps.user.utils.queries.user_db_query import UserDBQuery
from apps.user.utils.queries.user_storage_query import UserStorageQuery
from architecture.manager.backend_manager import CRUDManager
from architecture.manager.base_manager import FrontendManager
from core.exc import UserNotFound
from core.permissions import (
    PermissionAdminChecker as AdminOnly,
    PermissionIssueLoginChecker as LoginedOnly,
)
from core.token_generators import LoginTokenGenerator

class UserCRUDManager(CRUDManager):


    def create(
        self,
        email: str,
        name: str,
        passwd: str,
        storage_size: int,
        is_admin: bool = False,
    ) -> User:
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
            UserStorageQuery().create(user_id=user.id, force=True)
        except Exception as e:
            # 실패시 User 삭제
            UserDBQuery().destroy(user_id=user.id)
            raise e
        else:
            return user

    def update(self):
        raise NotImplementedError
    
    def read(
        self,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Optional[User]:
        return UserDBQuery().read(
            user_name=user_name,
            user_email=user_email,
            user_id=user_id,
        )

    def destroy(
        self,
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
    def search(self):
        raise NotImplementedError


class UserManager(FrontendManager):

    def create_user(
        self,
        token: str,
        email: str,
        name: str,
        passwd: str,
        storage_size: int
    ) -> User:
        try:
            # token에서 해당 유저 정보를 추출
            decoded_token = LoginTokenGenerator().decode(token)
            op_email = decoded_token['email']
            issue = decoded_token['iss']
        except Exception:
            raise PermissionError()
        # Email에 대한 User 데이터 가져오기
        operator: User = UserCRUDManager().read(user_email=op_email)
        if not operator:
            # 해당 Email에 대한 User가 없는 경우
            raise PermissionError()
        if not bool(AdminOnly(operator.is_admin) & LoginedOnly(issue)):
            # 관리자, 로그인 상태 둘 중 하나라도 아니면 Permisson Failed
            raise PermissionError()
        # User 생성을 위한 Create Format 생성
        return UserCRUDManager().create(
            email=email,
            name=name,
            passwd=passwd,
            storage_size=storage_size
        )

    def read_user(self, token: str, pk: str) -> User:
        try:
            # token에서 해당 유저 정보를 추출
            decoded_token = LoginTokenGenerator().decode(token)
            op_email = decoded_token['email']
            issue = decoded_token['iss']
        except Exception:
            raise PermissionError()
        # Email에 대한 유저가 존재하지 않으면 Permisson Failed
        operator: User = UserCRUDManager().read(user_email=op_email)
        if not operator:
            raise PermissionError()
        if not bool(LoginedOnly(issue)):
            # Login 상태가 아니면 Permisson Failed
            raise PermissionError()
        # User 검색, 없으면 None
        user: User = UserCRUDManager().read(user_id=pk)
        if not user:
            # 검색 대상의 사용자가 없음
            raise UserNotFound()
        return user
