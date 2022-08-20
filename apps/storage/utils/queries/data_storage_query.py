import os
import shutil
from typing import Dict, List, Optional
from fastapi import UploadFile
from sqlalchemy.sql import func

from architecture.query.crud import (
    QueryCRUD, 
    QueryCreator, 
    QueryDestroyer,
    QueryReader,
    QueryUpdator
)
from apps.storage.models import DataInfo
from apps.user.models import User
from core.exc import UsageLimited
from system.connection.generators import DatabaseGenerator


class DataStorageQueryCreator(QueryCreator):
    def __call__(
        self, 
        root: str, 
        is_dir: bool,
        rewrite: bool = False,
        file: Optional[UploadFile] = None,
        user_id: Optional[int] = None,
    ) -> int:
        """
        파일 또는 디렉토리 생성
        이미 존재하는 경우 AsertionError 호출

        :return: 데이터 길이 (디렉토리는 파일 0개이므로 0, 파일은 파일 크기)
        """
        if is_dir:
            # 디렉토리 생성
            # rewrite 여부 상관 없이 덮어쓰기 불가능
            assert os.path.isdir(root) is False
            os.mkdir(root)
            return 0
        else:
            # 파일 생성
            if rewrite:
                # rewrite를 하지 않는 경우
                assert os.path.isfile(root) is False
            
            segment_size = 1000 # 1000바이트씩 끊어서
            data_len = 0 # 데이터 길이
            with open(root, 'wb') as f:
                while s := file.file.read(segment_size):
                    f.write(s)
                    data_len += len(s)

            # 데이터 크기 비교
            
            try:
                session = DatabaseGenerator.get_session()
                entire = session.query(User) \
                    .filter(User.id == user_id) \
                    .scalar().storage_size * (10**9)    # GB단위이므로 바이트단위로 바꾼다.
                used = session.query(func.sum(DataInfo.size)) \
                    .filter(DataInfo.user_id == user_id) \
                    .group_by(DataInfo.user_id).scalar()
                if used + data_len > entire:
                    # 메모리 초과, 데이터 삭제 후 Exception
                    os.remove(root)
                    print('removed')
                    raise UsageLimited()
            except Exception as e:
                raise e
            else:
                return data_len
            finally:
                session.close()


            return data_len

class DataStorageQueryReader(QueryReader):
    def __call__(self, root: str, is_dir: bool) -> Optional[Dict]:
        if is_dir:
            # directory
            if not os.path.isdir(root):
                return None
            else:
                filenames: List[str] = os.scandir(root)
                files = []
                for filename in filenames:
                    f = {
                        'is_dir': None,
                        'filename': filename,
                    }
                    file_root = f'{root}/{filename}'
                    if os.path.isdir(file_root):
                        f['is_dir'] = True
                    else:
                        f['is_dir'] = False
                    files.append(f)
                return {
                    'size': len(files),
                    'files': files,
                }
        else:
            # file
            if not os.path.isfile(root):
                return None
            else:
                return {
                    'size': os.path.getsize(root),
                }

class DataStorageQueryDestroyer(QueryDestroyer):
    def __call__(self, root: str):
        if os.path.isfile(root):
            os.remove(root)
        elif os.path.isdir(root):
            shutil.rmtree(root)

class DataStorageQueryUpdator(QueryUpdator):
    def __call__(self, root: str, new_name: str) -> Optional[str]:
        if (os.path.isfile(root) or os.path.isdir(root)):
            root_list = root.split('/')
            root_list[-1] = new_name
            new_root = '/'.join(root_list)
            os.rename(root, new_root)   # 같은 이름이 존재할 경우 에러 발생
            return new_root
        else:
            return None

class DataStorageQuery(QueryCRUD):
    creator = DataStorageQueryCreator
    destroyer = DataStorageQueryDestroyer
    reader =  DataStorageQueryReader
    updator = DataStorageQueryUpdator
