import shutil
from typing import Any, Dict, List, Optional
from fastapi import UploadFile
from sqlalchemy import and_
import os
import datetime

from apps.storage.models import DataInfo
from apps.storage.schemas import DataInfoCreate, DataInfoUpdate
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

        :param root_id: 파일이 올라갈 디렉토리 아이디
        :param user_id: 사용자 아이디
        :param files: 올라갈 파일 데이터들

        :return: 생성된 데이터 리스트
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
            # 상위 디렉토리 절대경로 생성
            dir_root = f'{directory_info.root}{directory_info.name}/'
        
        # File 돌면서 차례대로 생성 및 덮어쓰기
        for file in files:
            filename = file.filename.split('/')[-1]
            # 파일 절대 경로 생성
            file_root = \
                f'{SERVER["storage"]}/storage/{user_id}/root{dir_root}{filename}'
            """
            같은 이름, 같은 루트, 같은 이용자의 파일관련 데이터가 있는 지
            확인하기.
            존재하는 경우는, 해당 파일이 부적절한 방법으로 지워진 경우이다.
            이때 DB 데이터를 삭제해서 에러호출을 하는 것이 아닌
            그냥 파일을 새로 만든다.

            단 같은 이름의 파일이 아닌 디렉토리인 경우, 이부분을 패스한다.
            """
            data_info: DataInfo = DataDBQuery().read(
                user_id=user_id, 
                full_root=(dir_root, filename),
            )
            if not data_info:
                # 없으면 새로 생성
                # 여기서 name이 잘못되면 ValidationError발생
                create_format: DataInfoCreate = DataInfoCreate(
                    name=filename,
                    user_id=user_id,
                    root=dir_root,
                    is_dir=False
                )
                try:
                    # DB 등록
                    data_info: DataInfo = DataDBQuery().create(create_format)
                except Exception:
                    # 에러발생시 Pass
                    continue
            else:
                if data_info.is_dir:
                    # 디렉토리가 등장하는 경우
                    # 생성하지 않고 무시
                    continue
            try:
                # 파일 생성
                # 기존에 존재하는 파일은 덮어쓴다.
                DataStorageQuery().create(root=file_root, is_dir=False, file=file)
            except Exception:
                # 실패 시 저장했던 DB 데이터를 삭제한다
                DataDBQuery().destroy(data_info.id)
                continue
            else:
                # 성공
                res.append(data_info)
        return res

    def read(self, raw_root: str) -> str:
        # 다운로드 할 때만 사용
        return raw_root

    def update(self, user_id: int, data_id: int, new_name: str):
        # User 확인
        user: User = UserDBQuery().read(user_id=user_id)
        if not user:
            raise UserNotFound()
        # 수정 대상 DataInfo 확인
        data: DataInfo = \
            DataDBQuery().read(user_id=user_id, data_id=data_id, is_dir=False)
        if not data:
            raise DataNotFound()
        # Validate 측정
        DataInfoUpdate(name=new_name, root=data.root, user_id=user_id)

        prev_name = data.name
        directory_root = f'{SERVER["storage"]}/storage/{user_id}/root{data.root}'
        raw_root = f'{directory_root}{prev_name}'
        try:
            # 파일 수정
            new_root = DataStorageQuery().update(raw_root, new_name)
        except Exception:
            """
            같은 이름의 파일 및 디렉토리가 있는 경우 발생
            업데이트 불가능
            """
            raise DataAlreadyExists()
        
        if not new_root:
            # raw_root가 스토리지에 존재하지 않음
            # DB상에서 삭제
            DataDBQuery().destroy(data_id)
            raise DataNotFound()
        
        try:
            # DB 데이터 수정
            res = DataDBQuery().update(
                data_info=data, 
                new_name=new_name, user_id=user_id
            )
        except Exception as e:
            # DB 데이터 수정에 에러 발생
            # Storage rollback
            DataStorageQuery().update(f'{directory_root}{new_name}', data.name)
            raise e
        return res

    def destroy(self, user_id: int, data_id: int):
        root, name = DataDBQuery().destroy(data_id)
        raw_root = \
            f'{SERVER["storage"]}/storage/{user_id}/root{root}{name}'
        DataStorageQuery().destroy(root=raw_root)
        

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
        db_record: DataInfo = DataDBQuery().read(
            user_id=user_id,
            is_dir=True,
            full_root=(dir_root, dirname)
        )

        # Storage에 데이터가 있는 지 확인
        root = f'{SERVER["storage"]}/storage/{user_id}/root{dir_root}{dirname}'
        storage_record = DataStorageQuery().read(root=root, is_dir=True)

        if db_record and storage_record:
            # 생성하고자 하는 디렉토리가 이미 존재하는 경우
            raise DataAlreadyExists()
        elif db_record:
            # DB에만 있고 Storage에는 없음
            # 해당 디렉토리의 하위의 모든 DB 삭제
            DataDBQuery().destroy(db_record.id)
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
            # 이 경우는 거의 없다고 가정
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
            DataStorageQuery().destroy(root)

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
                # 롤백
                DataDBQuery().destroy(db_record.id)
                raise e
            return db_record
        

    def update(self, user_id: int, data_id: int, new_name: str):
        # User 확인
        user: User = UserDBQuery().read(user_id=user_id)
        if not user:
            raise UserNotFound()
        # DataInfo 확인
        data: DataInfo = \
            DataDBQuery().read(user_id=user_id, data_id=data_id)
        if not data:
            raise DataNotFound()
        # Validate 측정
        DataInfoUpdate(name=new_name, root=data.root, user_id=user_id)

        prev_name = data.name
        directory_root = f'{SERVER["storage"]}/storage/{user_id}/root{data.root}'
        raw_root = f'{directory_root}{prev_name}'
        try:
            # 디렉토리 수정
            new_root = DataStorageQuery().update(raw_root, new_name)
        except Exception:
            """
            같은 이름의 파일 및 디렉토리가 있는 경우 발생
            업데이트 불가능
            """
            raise DataAlreadyExists()
        
        if not new_root:
            # raw_root가 스토리지에 존재하지 않음
            # DB상에서 삭제
            DataDBQuery().destroy(data_id)
            raise DataNotFound()
        
        try:
            # DB 데이터 수정
            res = DataDBQuery().update(
                data_info=data, new_name=new_name, user_id=user_id
            )
        except Exception as e:
            # DB 데이터 수정에 에러 발생
            # Storage 원상태 복구
            DataStorageQuery().update(f'{directory_root}{new_name}', prev_name)
            raise e
        return res

    def read(self, raw_root: str) -> str:
        # 다운로드 할 때만 사용

        # Zip File 생성
        tmp_name = f'download-{datetime.datetime.now().strftime("%Y%m%d-%H%M%S%f")}'
        tmp_zip = shutil.make_archive(tmp_name, 'zip', raw_root)
        return tmp_zip
    
    def destroy(self, user_id: int, data_id: int):
        root, name = DataDBQuery().destroy(data_id)
        raw_root = \
            f'{SERVER["storage"]}/storage/{user_id}/root{root}{name}'
        DataStorageQuery().destroy(root=raw_root)

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
        """
        파일/디렉토리 생성

        :param token: 인증용 토큰
        :param user_id: 사용자 아이디
        :param data_id: 데이터가 올라갈 상위 디렉토리 아이디
        :param request_files: 요청된 파일들
        :param req_dirname: 새로 생성할 디렉토리 이름

        :return: 새로 생성된 데이터의 리스트를 반환
        """
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

    def read(
        self, token: str, 
        user_id: int, 
        data_id: int, 
        mode: str = 'info'
    ) -> Dict[str, Any]:
        
        op_email, issue = decode_token(token, LoginTokenGenerator)
        operator: User = UserDBQuery().read(user_email=op_email)
        # 해당 User 없으면 PermissionError
        if not operator:
            raise PermissionError()
        # Admin이거나, client and 자기 자신이어야 한다
        if not bool(
            LoginedOnly(issue) & (
                AdminOnly(operator.is_admin) | 
                ((~AdminOnly(operator.is_admin)) & OnlyMine(operator.id, user_id))
            )
        ):
            raise PermissionError()

        if not UserDBQuery().read(user_id=user_id):
            # user_id에 대한 정보가 존재하는 지 확인
            raise UserNotFound()

        try:
            # DB에 데이터 검색
            data_info: DataInfo = \
                DataDBQuery().read(user_id=user_id, data_id=data_id)
        except Exception as e:
            raise e
        if not data_info:
            # 데이터 없음
            raise DataNotFound()

        # 실제 루트
        raw_root = \
            f'{SERVER["storage"]}/storage/{user_id}/root{data_info.root}{data_info.name}'

        # 스토리지 데이터 확인
        storage_info = \
            DataStorageQuery().read(
                root=raw_root, is_dir=data_info.is_dir)

        if not storage_info:
            # 실제 스토리지에 존재하지 않음
            DataDBQuery().destroy(data_info.id)
            raise DataNotFound()

        # 리턴 데이터
        res = {
            'info': {
                'root': data_info.root,
                'is_dir': data_info.is_dir,
                'name': data_info.name,
                'size': len(os.listdir(raw_root)) if data_info.is_dir \
                    else os.path.getsize(raw_root)
            }
        }

        if mode == 'download':
            # 다운로드 모드
            # 다운로드 대상의 파일 주소만 리턴
            if not data_info.is_dir:
                res['file'] = DataFileCRUDManager().read(raw_root)
            else:
                res['file'] = DataDirectoryCRUDManager().read(raw_root)
        return res
    
    def update(
        self, token: str, user_id: int, data_id: int, new_name: str
    ) -> Dict[str, Any]:
        
        # email에 대한 요청 사용자 구하기
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
            # 데이터 검색
            target: Optional[DataInfo] = \
                DataDBQuery().read(user_id=user_id, data_id=data_id)
            if not target:
                # 데이터 없음
                raise DataNotFound()
            if target.is_dir:
                # 디렉토리
                res = DataDirectoryCRUDManager() \
                    .update(user_id, data_id, new_name)
            else:
                # 파일
                res = DataFileCRUDManager() \
                    .update(user_id, data_id, new_name)
        except Exception as e:
            raise e
        else:
            return {
                'data_id': res.id,
                'root': res.root,
                'name': res.name,
                'is_dir': res.is_dir,
            }

    def destroy(self, token: str, user_id: int, data_id: int):

        # email에 대한 요청 사용자 구하기
        op_email, issue = decode_token(token, LoginTokenGenerator)
        operator: Optional[User] = \
            UserDBQuery().read(user_email=op_email)
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
            # 검색
            target: Optional[DataInfo] = \
                DataDBQuery().read(user_id=user_id, data_id=data_id)
            if not target:
                raise DataNotFound()
            elif target.is_dir:
                DataDirectoryCRUDManager().destroy(user_id, data_id)
            else:
                DataFileCRUDManager().destroy(user_id, data_id)
        except Exception as e:
            raise e
