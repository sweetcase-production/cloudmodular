from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy import and_

from apps.storage.models import DataInfo
from apps.storage.schemas import DataInfoCreate
from apps.storage.utils.queries.data_db_query import DataDBQuery
from apps.storage.utils.queries.data_storage_query import DataStorageQuery
from apps.user.models import User
from apps.user.utils.queries.user_db_query import UserDBQuery
from architecture.manager.backend_manager import CRUDManager
from core.exc import (
    DataAlreadyExists,
    DataNotFound,
    UserNotFound
)
from core.token_generators import LoginTokenGenerator
from core.permissions import (
    PermissionAdminChecker as AdminOnly,
    PermissionIssueLoginChecker as LoginedOnly,
)
from architecture.query.permission import (
    PermissionSameUserChecker as OnlyMine,
)
from architecture.manager.base_manager import FrontendManager
from settings.base import SERVER
from system.connection.generators import DatabaseGenerator

class DataFileCRUDManager(CRUDManager):

    def create(
        self, root_id: int, user_id: int, files: List[UploadFile]
    ) -> List[DataInfo]:
        """
        파일 생성
        
        동일한 이름의 파일이 존재하는 경우, 덮어쓴다.
        """
        res: List[DataInfo] = []

        # user 존재 여부 확인
        user: User = UserDBQuery().read(user_id=user_id)
        if not user:
            raise UserNotFound()
        
        dir_root = '/'  # 최상위 루트
        if root_id != 0:
            # id가 0인 경우는 최상위 루트이다.
            # 0이상인 경우만 DB에서 검색한다.
            directory_info: DataInfo =  DataDBQuery().read(
                user_id=user_id, data_id=root_id, 
                is_dir=True
            )
            if not directory_info:
                raise DataNotFound()
            dir_root = f'{directory_info.root}{directory_info.name}/'
        
        # File 돌면서 차례대로 생성 및 덮어쓰기
        for file in files:
            filename = file.filename.split('/')[-1]
            # native file_root 생성
            file_root = \
                f'{SERVER["storage"]}/storage/{user_id}/root{dir_root}{filename}'

            """
            같은 이름, 같은 루트, 같은 이용자의 파일관련 데이터가 있는 지
            확인하기.
            존재하는 경우는, 해당 파일이 부적절한 방법으로 지워진 경우이다.
            이때 DB 데이터를 삭제해서 에러호출을 하는 것이 아닌
            그냥 파일을 새로 만든다.
            """
            data_info: DataInfo = DataDBQuery().read(
                user_id=user_id, full_root=(dir_root, filename),
                is_dir=False
            )
            if not data_info:
                # 없으면 새로 생성
                create_format: DataInfoCreate = DataInfoCreate(
                    name=filename,
                    user_id=user_id,
                    root=dir_root,
                    is_dir=False
                )
                try:
                    data_info: DataInfo = DataDBQuery().create(create_format)
                except Exception:
                    # 에러발생시 Pass
                    # TODO 추후에 에러 상태를 출력 또는 저장하는 기능을 추가해야 한다.
                    continue
            try:
                # 파일 생성
                # 기존에 존재하는 파일은 덮어쓴다.
                DataStorageQuery().create(root=file_root, is_dir=False, file=file)
            except Exception as e:
                # 실패 시 저장했던 DB 데이터를 삭제한다
                DataDBQuery().destroy(data_info.id)
                continue
            else:
                # 성공
                res.append(data_info)
        return res

    def update(self, *args, **kwargs):
        raise NotImplementedError()
    
    def read(self, *args, **kwargs):
        raise NotImplementedError()
    
    def destroy(self, *args, **kwargs):
        raise NotImplementedError()

    def search(self, *args, **kwargs):
        raise NotImplementedError()

class DataDirectoryCRUDManager(CRUDManager):

    def create(self, root_id: int, user_id: int, dirname: str) -> DataInfo:

        # User 존재 여부 확인
        user: User = UserDBQuery().read(user_id=user_id)
        if not user:
            raise UserNotFound()

        # 루트 디렉토리 확인
        dir_root = '/'  # 최상위 루트
        if root_id != 0:
            # 최상위 루트가 아닌 경우
            # 직접 검색
            directory_info: DataInfo =  DataDBQuery().read(
                user_id=user_id, data_id=root_id, 
                is_dir=True
            )
            if not directory_info:
                raise DataNotFound()
            dir_root = f'{directory_info.root}{directory_info.name}/'
        
        # DB에 해당 루트의 데이터가 있는 지 확인
        db_record = DataDBQuery().read(
            user_id=user_id,
            is_dir=True,
            full_root=(dir_root, dirname)
        )

        # Storage에 데이터가 있는 지 확인
        root = f'{SERVER["storage"]}/storage/{user_id}/root{dir_root}{dirname}'
        storage_record = DataStorageQuery().read(
            root=root, is_dir=True)

        if db_record and storage_record:
            # 생성하고자 하는 디렉토리가 이미 존재하는 경우
            raise DataAlreadyExists()
        elif db_record:
            # DB에만 있고 Storage에는 없음
            session = DatabaseGenerator.get_session()
            query = session.query(DataInfo)
            try:
                # 해당 디렉토리의 하위의 모든 DB 삭제
                query.filter(and_(
                    DataInfo.user_id == user_id,
                    DataInfo.root.startswith(f'{dir_root}{dirname}/')
                )).delete(synchronize_session='fetch')
                session.commit()
            except Exception as e:
                raise e
            finally:
                session.close()

            try:
                # Storage만 생성
                DataStorageQuery().create(root=root, is_dir=True)
            except Exception as e:
                # 실패 시 Storage 삭제
                DataDBQuery().destroy(db_record.id)
                raise e
            return db_record
        elif storage_record:
            # Storage에만 있고 DB에는 없음
            # 해당 디렉토리의 하위 DB데이터 전부 다 삭제
            # 해당 디렉토리의 하위 파일 및 디렉토리 전부 다 삭제
            # TODO 하위 데이터까지 복구하는 프로세스를 목적으로 구현 필요
            session = DatabaseGenerator.get_session()
            query = session.query(DataInfo)
            try:
                # DB 삭제
                query.filter(and_(
                    DataInfo.user_id == user_id,
                    DataInfo.root.startswith(f'{dir_root}{dirname}/')
                )).delete(synchronize_session='fetch')
                session.commit()
            except Exception as e:
                raise e
            finally:
                session.close()
            # Storage 삭제
            DataStorageQuery().destroy(root=root, is_dir=True)

            # 다시 생성
            create_format: DataInfoCreate = DataInfoCreate(
                name=dirname,
                root=dir_root,
                user_id=user_id,
                is_dir=True
            )
            return DataDBQuery().create(create_format)
            
        else:
            # 정상적인 새로 생성
            # DB, Storage 생성
            db_record = DataDBQuery().create(DataInfoCreate(
                name=dirname,
                root=dir_root,
                user_id=user_id,
                is_dir=True
            ))
            try:
                DataStorageQuery().create(root=root, is_dir=True)
            except Exception as e:
                DataDBQuery().destroy(db_record.id)
                raise e
            return db_record
        

    def update(self, *args, **kwargs):
        raise NotImplementedError()
    
    def read(self, *args, **kwargs):
        raise NotImplementedError()
    
    def destroy(self, *args, **kwargs):
        raise NotImplementedError()

    def search(self, *args, **kwargs):
        raise NotImplementedError()


class DataManager(FrontendManager):

    def create(
        self,
        token: str,
        user_id: int,
        data_id: int,
        request_files: Optional[List[UploadFile]] = None,
        req_dirname: Optional[str] = None
    ) -> List[DataInfo]:
        
        # 토큰 정보 추출
        try:
            decoded_token = LoginTokenGenerator().decode(token)
            op_email = decoded_token['email']
            issue = decoded_token['iss']
        except Exception:
            raise PermissionError()
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

        if request_files:
            # 파일 업로드
            return DataFileCRUDManager().create(
                root_id=data_id,
                user_id=user_id,
                files=request_files
            )
        elif req_dirname:
            # 디렉토리 생성
            return [DataDirectoryCRUDManager().create(
                root_id=data_id,
                user_id=user_id,
                dirname=req_dirname
            )]