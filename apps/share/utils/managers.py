from datetime import timedelta, datetime
from apps.auth.utils.managers import AppAuthManager

from apps.share.models import DataShared
from apps.share.utils.queries import DataSharedQuery
from apps.storage.models import DataInfo
from apps.storage.utils.managers import DataManager
from apps.storage.utils.queries.data_db_query import DataDBQuery
from apps.user.models import User
from apps.user.utils.queries.user_db_query import UserDBQuery
from architecture.manager.base_manager import FrontendManager
from core.exc import DataIsAlreadyShared, DataIsNotShared, DataNotFound
from core.token_generators import LoginTokenGenerator, decode_token
from core.permissions import (
    PermissionAdminChecker as AdminOnly,
    PermissionIssueLoginChecker as LoginedOnly,
)
from architecture.query.permission import (
    PermissionSameUserChecker as OnlyMine,
)
from settings.base import SERVER

class DataSharedManager(FrontendManager):

    def set_data_shared(self, token: str, user_id: int, data_id: int):
        
        op_email, issue = decode_token(token, LoginTokenGenerator)
        operator: User = UserDBQuery().read(user_email=op_email)
        # 해덩 User가 없으면 Permission Failed
        if not operator:
            raise PermissionError()
        # Admin이거나, client and 자기 자신이어야 한다.
        if not bool(
            LoginedOnly(issue) & (
                AdminOnly(operator.is_admin) | 
                ((~AdminOnly(operator.is_admin)) & OnlyMine(operator.id, user_id))
            )
        ):
            raise PermissionError()

        # 데이터 확인
        data: DataInfo = DataDBQuery().read(user_id=user_id, data_id=data_id)
        if not data:
            raise DataNotFound()

        # 공유 상태 확인
        shared: DataShared = \
            DataSharedQuery().read(
                user_id=user_id, data_id=data_id
            )
        if not shared:
            # 처음 생성
            shared = DataSharedQuery().create(data_id)
        elif shared.is_active is False or \
            (shared.share_started + timedelta(seconds=SERVER['data-shared-length'] * 60)) <= datetime.now():
            # 비활성이거나 이미 만료된 상태
            shared = DataSharedQuery().update(shared.id, True)
        else:
            # 공유중
            raise DataIsAlreadyShared()
        return shared.id


    def unset_data_shared(self, token: str, user_id: int, data_id: int):
        op_email, issue = decode_token(token, LoginTokenGenerator)
        operator: User = UserDBQuery().read(user_email=op_email)
        # 해덩 User가 없으면 Permission Failed
        if not operator:
            raise PermissionError()
        # Admin이거나, client and 자기 자신이어야 한다.
        if not bool(
            LoginedOnly(issue) & (
                AdminOnly(operator.is_admin) | 
                ((~AdminOnly(operator.is_admin)) & OnlyMine(operator.id, user_id))
            )
        ):
            raise PermissionError()
        
        # 데이터 확인
        data: DataInfo = DataDBQuery().read(user_id=user_id, data_id=data_id)
        if not data:
            raise DataNotFound()
        
        # 공유 상태 확인
        shared: DataShared = \
            DataSharedQuery().read(
                user_id=user_id, data_id=data_id
            )
        
        if not shared or not shared.is_active:
            raise DataIsNotShared()
        if shared.share_started + timedelta(seconds=SERVER['data-shared-length'] * 60) <= datetime.now():
            raise DataIsNotShared()
        else:
            DataSharedQuery().update(shared.id, False)
        

    def get_shared_id(self, token: str, user_id: int, data_id: int):
        op_email, issue = decode_token(token, LoginTokenGenerator)
        operator: User = UserDBQuery().read(user_email=op_email)
        # 해덩 User가 없으면 Permission Failed
        if not operator:
            raise PermissionError()
        # Admin이거나, client and 자기 자신이어야 한다.
        if not bool(
            LoginedOnly(issue) & (
                AdminOnly(operator.is_admin) | 
                ((~AdminOnly(operator.is_admin)) & OnlyMine(operator.id, user_id))
            )
        ):
            raise PermissionError()
        # 데이터 확인
        data: DataInfo = DataDBQuery().read(user_id=user_id, data_id=data_id)
        if not data:
            raise DataNotFound()
        
        # 공유 상태 확인
        shared: DataShared = \
            DataSharedQuery().read(
                user_id=user_id, data_id=data_id
            )
        if not shared or not shared.is_active:
            raise DataIsNotShared()
        if shared.share_started + timedelta(seconds=SERVER['data-shared-length'] * 60) \
            <= datetime.now():
            raise DataIsNotShared()
        else:
            return shared.id

    def get_info_of_shared_data(sef, shared_id: int):
        # Shared 정보 갖고오기
        shared: DataShared = DataSharedQuery().read(shared_id=shared_id)
        # 공유 여부 체크
        if not shared or not shared.is_active:
            raise DataIsNotShared()
        if shared.share_started + timedelta(seconds=SERVER['data-shared-length'] * 60) \
            <= datetime.now():
            raise DataIsNotShared()
        # Data 정보 가지고 오기
        data_info = DataDBQuery().read(data_id=shared.datainfo_id)
        if not data_info:
            raise DataNotFound()
        # Return
        return {
            'root': data_info.root,
            'name': data_info.name,
            'is_dir': data_info.is_dir,
        }

    def download_shared_data(self, shared_id: int):
        shared: DataShared = DataSharedQuery().read(shared_id=shared_id)
        # 공유 여부 체크
        if not shared or not shared.is_active:
            raise DataIsNotShared()
        if shared.share_started + timedelta(seconds=SERVER['data-shared-length'] * 60) \
            <= datetime.now():
            raise DataIsNotShared()

        # DataInfo 체크
        data_info = DataDBQuery().read(data_id=shared.datainfo_id)

        # Admin 권한으로 다운받는다.
        admin_user = UserDBQuery().read(is_admin=True)
        admin_token = AppAuthManager() \
            .login(admin_user.email, admin_user.passwd)
        download_root = \
            DataManager().read(admin_token, data_info.user_id, shared.datainfo_id, 'download')
        return download_root['file'], data_info.is_dir