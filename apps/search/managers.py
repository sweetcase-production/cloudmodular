from typing import Optional
from datetime import timedelta, datetime
from sqlalchemy import and_, func


from apps.data_tag.models import DataTag
from apps.share.models import DataShared
from apps.storage.models import DataInfo
from apps.storage.utils.queries.data_db_query import DataDBQuery
from apps.tag.models import Tag
from apps.user.models import User
from apps.user.utils.managers import UserCRUDManager
from apps.user.utils.queries.user_db_query import UserDBQuery
from architecture.manager.base_manager import FrontendManager
from core.token_generators import LoginTokenGenerator, decode_token
from settings.base import SERVER
from system.connection.generators import DatabaseGenerator

from core.permissions import (
    PermissionAdminChecker as AdminOnly,
    PermissionIssueLoginChecker as LoginedOnly,
)
from architecture.query.permission import (
    PermissionSameUserChecker as OnlyMine,
)


class DataSearchManager(FrontendManager):
    def search(
        self, token: str,
        user: str,                      # 사용자 이름
        root: Optional[str] = None,     # 탐색 위치(디렉토리만)
        root_id: Optional[int] = None,  # 탐색 위치(디렉토리 아이디)
        recursive: int = 0,             # 하위 부분까지 전부 탐색
        favorite: int = 0,              # 즐겨찾기 여부
        shared: int = 0,                # 공유 여부
        tags: Optional[str] = None,     # 태그가 포함된 데이터만
        word: Optional[str] = None,     # 연관검색어
        sort_create: int = 0,           # 생성 순 정렬
        sort_name: int = 0,             # 이름 순 정렬
    ):

        # token checking
        op_email, issue = decode_token(token, LoginTokenGenerator)
        operator: User = UserDBQuery().read(user_email=op_email)
        # 해덩 User가 없으면 Permission Failed
        if not operator:
            raise PermissionError()
        # Admin이거나, client and 자기 자신이어야 한다.
        if not bool(
            LoginedOnly(issue) & (
                AdminOnly(operator.is_admin) | 
                ((~AdminOnly(operator.is_admin)) & OnlyMine(operator.name, user))
            )
        ):
            raise PermissionError()

        # User 탐색
        if not (user_value := UserCRUDManager().read(user_name=user)):
            # 해당 유저가 없으면 검색 결과가 없는 것으로 설정
            return []
        # 대상 data 탐색
        if (not root) and (root_id is None):
            # root, root_id 둘 중에 하나 있어야 한다.
            raise ValueError()
        if root_id is not None:
            # root_id가 주어져 있는 경우
            if root_id == 0:
                root = '/'
            else:
                root_info: DataInfo = DataDBQuery().read(user_id=user_value.id, data_id=root_id)
                if not root_info or (not root_info.is_dir):
                    # 데이터 없음 or 디렉토리가 아님
                    return []
                root = f'{root_info.root}{root_info.name}/'
        else:
            # Root가 주어져 있는 경우
            if root != '/':
                # Root Checking
                splited = root[:-1].split('/')
                root_query = ['/'.join(splited[:-1]) + '/', splited[-1]]
                data_value = DataDBQuery().read(full_root=root_query, is_dir=True)
                if not data_value:
                    return []
        # 검색 시작
        shared_len = SERVER['data-shared-length']
        session = DatabaseGenerator.get_session()
        query = session.query(DataInfo, DataShared)
        query = query.outerjoin(DataShared)
        # 해당 사용자의 데이터만
        query = query.filter(DataInfo.user_id == user_value.id)
        # Recursive 여부
        query = query.filter(DataInfo.root == root) if not recursive \
            else query.filter(DataInfo.root.startswith(root))        
        if favorite:
            # 즐겨찾기 여부
            query = query.filter(DataInfo.is_favorite == True)
        if word:
            # 연관검색어
            query = query.filter(DataInfo.name.contains(word))
        if shared:
            # 공유 여부
            left_time = (datetime.now() - timedelta(minutes=shared_len)).strftime('%Y-%m-%d')
            right_time = '2200-01-01'
            query = query.filter(and_(
                    DataShared.is_active == True,
                    DataShared.share_started.between(left_time, right_time)
                ))
        if tags:
            # 태그 검색
            tag_list = tags.split(',')
            query = query.join(DataTag, DataTag.datainfo_id == DataInfo.id)
            query = query.join(Tag, Tag.id == DataTag.tag_id)
            query = query.filter(Tag.name.in_(tag_list))
        # 정렬시 디렉토리 - 파일 순 정렬은 필수
        if sort_name and sort_create:
            # 이름, 생성 순 정렬
            query = query.order_by(
                DataInfo.is_dir.desc(), 
                DataInfo.created.asc(), 
                DataInfo.name.asc()
            )
        elif sort_name:
            query = query.order_by(
                DataInfo.is_dir.desc(), 
                DataInfo.name.asc()
            )
        elif sort_create:
            query = query.order_by(
                DataInfo.is_dir.desc(), 
                DataInfo.created.asc()
            )
        records = query.all()
        res = list()
        for data, shared in records:
            shared_id = -1
            if shared:
                # 공유 ID 구하기
                # 공유 상태가 아닌 경우 -1
                shared_id = shared.id
                if shared.is_active \
                    and shared.share_started + timedelta(minutes=shared_len) >= datetime.now():
                    shared_id = shared.id
            res.append({
                'id': data.id,
                'root': data.root,
                'is_dir': data.is_dir,
                'name': data.name,
                'is_favorite': data.is_favorite,
                'shared_id': shared_id
            })
        

        return res