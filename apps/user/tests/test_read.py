import pytest
import os
from fastapi import status
from fastapi.testclient import TestClient

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
    admin = UserCRUDManager().create(**admin_info)
    admin_info['id'] = admin.id
    # Add Client
    client_info = {
        'email': 'seokbong61@gmail.com',
        'name': 'jeonghyun2',
        'passwd': 'passwd0123',
        'storage_size': 10,
    }
    client = UserCRUDManager().create(**client_info)
    client_info['id'] = client.id
    # Return test api
    yield TestClient(app)
    # Remove All Of Data
    Bootloader.remove_storage()
    Bootloader.remove_database()

def test_no_token(api: TestClient):
    res = api.get(f'/api/users/{admin_info["id"]}')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_uo_user(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.get(f'/api/users/0', headers={'token': token})
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_success(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    
    res = api.get(f'/api/users/{admin_info["id"]}', headers={'token': token})
    assert res.status_code == status.HTTP_200_OK

