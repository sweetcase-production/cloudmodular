from fastapi import status
from fastapi.testclient import TestClient
import pytest

from main import app
from system.bootloader import Bootloader
from apps.user.utils.managers import UserCRUDManager

user_info = None

@pytest.fixture(scope='module')
def api():
    global user_info
    # Load Application
    Bootloader.migrate_database()
    Bootloader.init_storage()
    # Add User
    user_info = {
        'email': 'seokbong60@gmail.com',
        'name': 'jeonhyun',
        'passwd': 'password0123',
        'storage_size': 5
    }
    # 테스트 대상의 사용자 생성
    user = UserCRUDManager().create(**user_info)
    user_info['id'] = user.id
    # Test용 api 리턴
    yield TestClient(app)
    # Remove Application
    Bootloader.remove_storage()
    Bootloader.remove_database()

def test_success_get_login_token(api: TestClient):
    email, passwd = user_info['email'], user_info['passwd']
    req = {
        'issue': 'login',
        'passwd': passwd,
        'email': email,
    }
    res = api.post('/api/auth/token', json=req)
    assert res.status_code == status.HTTP_201_CREATED
    assert 'token' in res.json()
    assert res.json()['user_id'] == user_info['id']

def test_passwd_failed_while_get_login_token(api: TestClient):
    email = user_info['passwd']
    req = {
        'issue': 'login',
        'passwd': "a????",
        'email': email,
    }
    res = api.post('/api/auth/token', json=req)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.json()['detail'] == '입력한 정보가 맞지 않습니다.'
