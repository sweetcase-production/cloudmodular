from datetime import datetime
from pydantic import BaseModel, validator


class DataInfoBase(BaseModel):
    name: str
    root: str

    @staticmethod
    def _check_filename(s: str):
        no_uses = {'/', '\\', ':', '*', '"', "'", '<', '>', '|'}
        return (not s) or (not any([c in s for c in no_uses]))

    @validator('name')
    def validate_name(cls, name: str):
        if not DataInfoBase._check_filename(name):
            raise ValueError('파일 또는 폴더 이름이 유효하지 않습니다.')
        return name

    @validator('root')
    def validate_root(cls, root: str):
        if root == '/':
            # 최상위 루트
            return root
        units = root.split('/')
        for unit in units:
            if not DataInfoBase._check_filename(unit):
                raise ValueError('폴더 이름이 유효하지 않습니다.')
        return root


class DataInfoCreate(DataInfoBase):
    is_dir: bool
    user_id: int
    size: int

class DataInfoUpdate(DataInfoBase):
    user_id: int

class DataInfoRead(DataInfoBase):
    size: int
    is_dir: bool
    created: datetime
    id: int

    class Config:
        orm_mode = True