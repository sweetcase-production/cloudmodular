from pydantic import BaseModel, validator
from pydantic import validate_email as check_email
import re
import datetime


def _validate_email(cls, email: str):
    check_email(email)
    if len(email) > 255:
        raise ValueError('Email의 길이가 너무 깁니다.')
    return email

def _validate_name(cls, name: str):
    # 알파벳 또는 숫자
    if not re.compile(r'^[a-zA-Z0-9]{4,32}$').match(name):
        raise ValueError('알맞은 이름이 아닙니다.')
    return name

def _validate_storage_size(cls, storage_size: int):
    # 1 GB이상 20GB 이하 (차후에 변경 예정)
    if not (1 <= storage_size <= 20):
        raise ValueError('용량 크기가 맞지 않습니다.')
    return storage_size

def _validate_passwd(cls, passwd: str):
    # 8자 이상
    if not (8 <= len(passwd) <= 32):
        raise ValueError('패스워드가 맞지 않습니다.')
    return passwd

class UserBase(BaseModel):
    name: str

    @validator('name')
    def validate_name(cls, name: str):
        return _validate_name(cls, name)

class UserCreate(UserBase):
    
    storage_size: int
    is_admin: bool
    email: str
    passwd: str

    @validator('passwd')
    def validate_passwd(cls, passwd: str):
        return _validate_passwd(cls, passwd)

    @validator('storage_size')
    def validate_storage_size(cls, storage_size: int):
        return _validate_storage_size(cls, storage_size)
    
    @validator('email')
    def validate_email(cls, email: str):
        return _validate_email(cls, email)

class UserRead(UserBase):

    storage_size: int
    is_admin: bool
    email: str
    id: int
    created: datetime.datetime

    @validator('storage_size')
    def validate_storage_size(cls, storage_size: int):
        return _validate_storage_size(cls, storage_size)
    
    @validator('email')
    def validate_email(cls, email: str):
        return _validate_email(cls, email)

    class Config:
        orm_mode = True
