import pytest
import os
from fastapi import status
from fastapi.testclient import TestClient
import threading

from main import app
from system.bootloader import Bootloader
from apps.auth.utils.managers import AppAuthManager
from apps.user.utils.managers import UserCRUDManager

admin_info = None
client_info = None

@pytest.fixture(scope='module')
def api():
    global admin_info
    global client_info
    # Load Application
    Bootloader.migrate_database()
    Bootloader.init_storage()
    # Add Admin
    admin_info = {
        'email': 'seokbong60@gmail.com',
        'name': 'jeonhyun',
        'passwd': 'password0123',
        'storage_size': 5,
        'is_admin': True,
    }
    UserCRUDManager().create(**admin_info)
    # Add Client
    client_info = {
        'email': 'seokbong61@gmail.com',
        'name': 'jeonghyun2',
        'passwd': 'passwd0123',
        'storage_size': 10,
    }
    a = UserCRUDManager().create(**client_info)
    # Return test api
    yield TestClient(app)
    # Remove All Of Data
    Bootloader.remove_storage()
    Bootloader.remove_database()

def test_failed_because_no_login(api: TestClient):
    req = {
        'email': 'themail@gmail.com',
        'name': 'JooHyun',
        'passwd': 'passwd01234',
        'storage_size': 4,
    }
    res = api.post('/api/user', json=req)
    res.status_code = status.HTTP_403_FORBIDDEN

def test_all_omit_req_data(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post('/api/user', headers={'token': token})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_some_omit_req_data(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    req = {
        'email': 'themail@gmail.com',
        'name': 'JooHyun',
        'storage_size': 4,
    }
    res = api.post('/api/user', json=req, headers={'token': token})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_failed_no_admin(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    req = {
        'email': 'themail@gmail.com',
        'name': 'JooHyun',
        'passwd': 'passwd01234',
        'storage_size': 4,
    }
    res = api.post('/api/user', json=req, headers={'token': token})
    assert res.status_code == status.HTTP_403_FORBIDDEN

"""
TODO 다른 형태의 token발행 기능 구현하면 작성 예정
def test_failed_token_is_no_login_issue(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
"""

def test_email_validation_failed(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    req = {
        'email': 'themail.gmail.com',
        'name': 'JooHyun',
        'passwd': 'passwd01234',
        'storage_size': 4,
    }
    res = api.post('/api/user', json=req, headers={'token': token})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_name_validation_failed(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    req = {
        'email': 'themail@gmail.com',
        'name': 'a'*3,
        'passwd': 'passwd01234',
        'storage_size': 4,
    }
    res = api.post('/api/user', json=req, headers={'token': token})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    req['name'] = 'a'* 33
    res = api.post('/api/user', json=req, headers={'token': token})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    req['name'] = 'aaa안aaa'
    res = api.post('/api/user', json=req, headers={'token': token})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_passwd_validation_failed(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    req = {
        'email': 'themail@gmail.com',
        'name': 'user001',
        'passwd': 'p'*7,
        'storage_size': 4,
    }
    res = api.post('/api/user', json=req, headers={'token': token})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    req['passwd'] = 'p' * 33
    res = api.post('/api/user', json=req, headers={'token': token})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_storage_size_validation_failed(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    req = {
        'email': 'themail@gmail.com',
        'name': 'user001',
        'passwd': 'passwd01',
        'storage_size': 0,
    }
    res = api.post('/api/user', json=req, headers={'token': token})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_failed_same_data(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    req = {
        'email': client_info['email'],
        'name': 'user001',
        'passwd': 'passwd01',
        'storage_size': 5,
    }
    res = api.post('/api/user', json=req, headers={'token': token})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    req = {
        'email': 'themail@gmail.com',
        'name': client_info['name'],
        'passwd': 'passwd01',
        'storage_size': 5,
    }
    res = api.post('/api/user', json=req, headers={'token': token})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_success(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    req = {
        'email': 'themail@gmail.com',
        'name': 'user001',
        'passwd': 'passwd01',
        'storage_size': 5,
    }
    res = api.post('/api/user', json=req, headers={'token': token})
    assert res.status_code == status.HTTP_201_CREATED

    # 디렉토리 확인
    from settings.base import SERVER
    main_root = f'{SERVER["storage"]}/storage/{res.json()["id"]}'
    
    assert os.path.isdir(main_root)
