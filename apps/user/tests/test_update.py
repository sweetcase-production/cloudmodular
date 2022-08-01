from unittest import TestCase
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from system.bootloader import Bootloader
from apps.auth.utils.managers import AppAuthManager
from apps.user.utils.managers import UserCRUDManager
from apps.user.models import User

admin_info = None
client_info1 = None
client_info2 = None

@pytest.fixture(scope='module')
def api():
    global admin_info
    global client_info1
    global client_info2
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
    admin = UserCRUDManager().create(**admin_info)
    admin_info['id'] = admin.id
    # Add Client1
    client_info1 = {
        'email': 'seokbong61@gmail.com',
        'name': 'jeonghyun2',
        'passwd': 'passwd0123',
        'storage_size': 10,
    }
    client = UserCRUDManager().create(**client_info1)
    client_info1['id'] = client.id
    # Add Client2
    client_info2 = {
        'email': 'seokbong62@gmail.com',
        'name': 'jeonghyun3',
        'passwd': 'passwd0123',
        'storage_size': 10,
    }
    client = UserCRUDManager().create(**client_info2)
    client_info2['id'] = client.id
    # Return test api
    yield TestClient(app)
    # Remove All Of Data
    Bootloader.remove_storage()
    Bootloader.remove_database()

def test_no_token(api: TestCase):
    res = api.patch(f'/api/users/{client_info1["id"]}')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_not_admin(api: TestCase):
    email, passwd = client_info1['email'], client_info1['passwd']
    token = AppAuthManager().login(email, passwd)

    req = {
        'name': 'changed1',
        'passwd': 'passwd134',
    }
    res = api.patch(
        f'/api/users/{client_info2["id"]}', 
        json=req, headers={'token': token}
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_omit_all_req(api: TestCase):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.patch(
        f'/api/users/{client_info1["id"]}',
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_omit_some_req(api: TestCase):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)

    req = dict()
    res = api.patch(
        f'/api/users/{client_info1["id"]}',
        headers={'token': token},
        json=req
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    req['passwd'] = 'abcdefsfd'
    res = api.patch(
        f'/api/users/{client_info1["id"]}',
        headers={'token': token},
        json=req
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_user_not_exists(api: TestCase):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)

    req = {
        'name': 'changed1',
        'passwd': 'passwd134',
    }
    res = api.patch(
        f'/api/users/0',
        json=req, headers={'token': token}
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_name_validation_failed(api: TestCase):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)

    req = {
        'name': 'a'*3,
        'passwd': 'passwd134',
    }
    res = api.patch(
        f'/api/users/{client_info1["id"]}',
        json=req, headers={'token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    req['name'] = 'a'*33
    res = api.patch(
        f'/api/users/{client_info1["id"]}',
        json=req, headers={'token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    req['name'] = 'aaaㅎㅇaaa'
    res = api.patch(
        f'/api/users/{client_info1["id"]}',
        json=req, headers={'token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_passwd_validation_failed(api: TestCase):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)

    req = {
        'name': 'changed1',
        'passwd': 'a'*7,
    }
    res = api.patch(
        f'/api/users/{client_info1["id"]}',
        json=req, headers={'token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    req['passwd'] = 'a'*33
    res = api.patch(
        f'/api/users/{client_info1["id"]}',
        json=req, headers={'token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_change_success(api: TestCase):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    
    req = {
        'name': 'changed1',
        'passwd': 'passwd134',
    }
    res = api.patch(
        f'/api/users/{client_info1["id"]}',
        json=req, headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    # 변경된 정보 확인
    user_data: User = UserCRUDManager().read(user_email=client_info1['email'])
    assert user_data.name == req['name']
    assert user_data.passwd == req['passwd']


def test_change_only_name(api: TestCase):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    
    req = {
        'name': 'changed2',
    }
    res = api.patch(
        f'/api/users/{client_info1["id"]}',
        json=req, headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    user_data: User = UserCRUDManager().read(user_email=client_info1['email'])
    assert user_data.name == req['name']