import os
import shutil

from typing import Optional
from fastapi import UploadFile
from architecture.query.crud import (
    QueryCRUD, 
    QueryCreator, 
    QueryDestroyer
)


class DataStorageQueryCreator(QueryCreator):
    def __call__(
        self, 
        root: str, 
        is_dir: bool,
        rewrite: bool = False,
        file: Optional[UploadFile] = None
    ):
        """
        파일 또는 디렉토리 생성
        이미 존재하는 경우 AsertionError 호출
        """
        if is_dir:
            # 디렉토리 생성
            # rewrite 여부 상관 없이 덮어쓰기 불가능
            assert os.path.isdir(root) is False
            os.mkdir(root)
        else:
            # 파일 생성
            if rewrite:
                # rewrite를 하지 않는 경우
                assert os.path.isfile(root) is False
            
            segment_size = 1000 # 1000바이트씩 끊어서
            with open(root, 'wb') as f:
                while s := file.file.read(segment_size):
                    f.write(s)

class DataStorageQueryDestroyer(QueryDestroyer):
    def __call__(self, root: str, is_dir: bool):
        if is_dir:
            if os.path.isdir(root):
                shutil.rmtree(root)
        else:
            if os.path.isfile(root):
                os.remove(root)

class DataStorageQuery(QueryCRUD):
    creator = DataStorageQueryCreator
    destroyer: DataStorageQueryDestroyer
