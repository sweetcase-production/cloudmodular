from typing import List, Optional

from apps.user.models import User
from apps.user.utils.queries.user_db_query import UserDBQuery
from apps.data_favorite.utils.query.data_favorite_query import DataFavoriteQuery
from apps.storage.models import DataInfo
from architecture.manager.base_manager import FrontendManager
from core.exc import DataFavoriteNotSelected, DataIsAlreadyFavorited
from core.token_generators import (
    LoginTokenGenerator,
    decode_token,
)
from core.permissions import (
    PermissionAdminChecker as AdminOnly,
    PermissionIssueLoginChecker as LoginedOnly,
)
from architecture.query.permission import (
    PermissionSameUserChecker as OnlyMine,
)

class DataFavoriteManager(FrontendManager):
    """
    즐겨찾기 설정
    """
    
    def set_favorite(
        self, token: str, user_id: int, data_id: int
    ):
        """
        즐겨찾기 설정

        :param token: 사용자 토큰
        :param user_id: 유저 아이디
        :param data_id: 해당 data_id
        """

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

        try:
            DataFavoriteQuery().update(user_id, data_id, True)
        except ValueError:
            # 이미 설정되어 있음
            raise DataIsAlreadyFavorited()
        except Exception as e:
            raise e

    def unset_favorite(
        self, token: str, user_id: int, data_id: int
    ):
        """
        즐겨찾기 해제

        :param token: 사용자 토큰
        :param user_id: 유저 아이디
        :param data_id: 해당 data_id
        """

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

        try:
            DataFavoriteQuery().update(user_id, data_id, False)
        except ValueError:
            # 이미 설정되어 있음
            raise DataFavoriteNotSelected()
        except Exception as e:
            raise e