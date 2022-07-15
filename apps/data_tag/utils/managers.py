from typing import Any, Optional, List

from apps.user.models import User
from apps.tag.models import Tag
from apps.data_tag.utils.queries import DataTagQuery
from apps.user.utils.queries.user_db_query import UserDBQuery
from architecture.manager.base_manager import FrontendManager
from core.token_generators import LoginTokenGenerator, decode_token
from core.permissions import (
    PermissionAdminChecker as AdminOnly,
    PermissionIssueLoginChecker as LoginedOnly,
)
from architecture.query.permission import (
    PermissionSameUserChecker as OnlyMine,
)

class DataTagManager(FrontendManager):
    
    def create_tags(self, token: str, user_id: int, data_id: int, tags: Any):
        
        # 요청 사용자 구하기
        op_email, issue = decode_token(token, LoginTokenGenerator)
        operator: Optional[User] = UserDBQuery().read(user_email=op_email)
        if not operator:
            raise PermissionError()

        # Admin이거나 client and 자기 자신이어야 한다
        if not bool(
            LoginedOnly(issue) & (
                AdminOnly(operator.is_admin) | 
                ((~AdminOnly(operator.is_admin)) & OnlyMine(operator.id, user_id))
            )
        ):
            raise PermissionError()

        if not isinstance(tags, list):
            # Tag는 반드시 List여야 한다.
            raise ValueError('Tag list must be List')

        result_tags: List[Tag] = DataTagQuery().create(data_id, tags)
        res = list()
        for tag in result_tags:
            res.append({'tag_name': tag.name})
        return res

    def get_tag_from_data(self, token: str, user_id: int, data_id: int):
        
        # 요청 사용자 구하기
        op_email, issue = decode_token(token, LoginTokenGenerator)
        operator: Optional[User] = UserDBQuery().read(user_email=op_email)
        if not operator:
            raise PermissionError()

        # Admin이거나 client and 자기 자신이어야 한다
        if not bool(
            LoginedOnly(issue) & (
                AdminOnly(operator.is_admin) | 
                ((~AdminOnly(operator.is_admin)) & OnlyMine(operator.id, user_id))
            )
        ):
            raise PermissionError()
        
        return [{'tag_name': tag.name} for tag in DataTagQuery().read(data_id)]