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
    res = api.delete(f'/api/user/{admin_info["id"]}')
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_no_admin(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    
    res = api.delete(f'/api/user/{admin_info["id"]}', headers={'Token': token})
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_user_not_exists(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.delete(f'/api/user/0', headers={'Token': token})
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_success(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.delete(f'/api/user/{client_info["id"]}', headers={'Token': token})
    assert res.status_code == status.HTTP_204_NO_CONTENT

    # 부검
    # 디렉토리가 아직 남아있는 지 확인
    from settings.base import SERVER
    main_root = f'{SERVER["storage"]}/storage'
    root = f'{main_root}/{client_info["id"]}'
    # 상위 디렉토리가 지워지지 말아야 한다
    assert os.path.isdir(main_root)
    # 유저 디렉토리는 지워저야 한다
    assert not os.path.isdir(root)
    # DB 상태도 삭제되어야 한다
    res = api.get(f'/api/user/{client_info["id"]}', headers={'Token': token})
    assert res.status_code == status.HTTP_404_NOT_FOUND
    # 삭제 요청 시 404가 떠야 한다.
    res = api.delete(f'/api/user/{client_info["id"]}', headers={'Token': token})
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_remove_admin_user(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.delete(f'/api/user/{admin_info["id"]}', headers={'Token': token})
    assert res.status_code == status.HTTP_403_FORBIDDEN
