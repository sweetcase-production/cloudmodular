from pydantic import BaseModel, validator
from pydantic import validate_email as check_email
import re
import datetime

class UserBase(BaseModel):

    email: str
    name: str
    storage_size: int
    is_admin: bool

    @validator('email')
    def validate_email(cls, email: str):
        check_email(email)
        if len(email) > 255:
            raise ValueError('Email의 길이가 너무 깁니다.')
        return email

    @validator('name')
    def validate_name(cls, name: str):
        # 알파벳 또는 숫자
        if not re.compile(r'^[a-zA-Z0-9]{4,32}$').match(name):
            raise ValueError('알맞은 이름이 아닙니다.')
        return name

    @validator('storage_size')
    def validate_storage_size(cls, storage_size: int):
        # 1 GB이상 20GB 이하 (차후에 변경 예정)
        if not (1 <= storage_size <= 20):
            raise ValueError('용량 크기가 맞지 않습니다.')
        return storage_size

class UserCreate(UserBase):
    passwd: str

    @validator('passwd')
    def validate_passwd(cls, passwd: str):
        # 8자 이상
        if not (8 <= len(passwd) <= 32):
            raise ValueError('패스워드가 맞지 않습니다.')
        return passwd


class UserRead(UserBase):
    id: int
    created: datetime.datetime
    
    class Config:
        orm_mode = True