from fastapi import UploadFile, status
import pytest
from fastapi.testclient import TestClient

from main import app
from apps.user.utils.managers import UserCRUDManager
from system.bootloader import Bootloader
from apps.auth.utils.managers import AppAuthManager
from apps.storage.utils.managers import DataFileCRUDManager


client_info, admin_info, other_info = None, None, None
file_id = 0
TEST_EXAMLE_ROOT = 'apps/storage/tests/example'

@pytest.fixture(scope='module')
def api():
    global client_info, admin_info, other_info
    global file_id
    # Load Application
    Bootloader.migrate_database()
    Bootloader.init_storage()
    # Add Account
    client_info = {
        'email': 'seokbong60@gmail.com',
        'name': 'jeonhyun',
        'passwd': 'password0123',
        'storage_size': 5,
    }
    user = UserCRUDManager().create(**client_info)
    client_info['id'] = user.id
    # Add Admin Info
    admin_info = {
        'email': 'seokbong61@gmail.com',
        'name': 'jeonhyun2',
        'passwd': 'password0123',
        'storage_size': 5,
        'is_admin': True,
    }
    user = UserCRUDManager().create(**admin_info)
    admin_info['id'] = user.id

    # Add Other Info
    other_info = {
        'email': 'seokbong62@gmail.com',
        'name': 'jeonhyun3',
        'passwd': 'password0123',
        'storage_size': 5,
    }
    user = UserCRUDManager().create(**other_info)
    other_info['id'] = user.id
    # Add File
    hi = open(f'{TEST_EXAMLE_ROOT}/hi.txt', 'rb')
    files = DataFileCRUDManager().create(
        root_id=0,
        user_id=client_info["id"],
        file=UploadFile(filename=hi.name, file=hi)
    )
    file_id = files.id

    yield TestClient(app)

    hi.close()
    Bootloader.remove_storage()
    Bootloader.remove_database()

def test_no_token(api: TestClient):
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{file_id}/tags',
        json={"tags": ["tag1", "tag2"]}
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_other_access_failed(api: TestClient):
    email, passwd = other_info['email'], other_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{file_id}/tags',
        headers={'token': token},
        json={"tags": ["tag1", "tag2"]}
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_wrong_params(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{file_id}/tags',
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{file_id}/tags',
        json={},
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{file_id}/tags',
        json={'xxcfd': 'xcfds'},
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{file_id}/tags',
        json={'tags': 1},
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_file_no_exists(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/99999999/tags',
        headers={'token': token},
        json={"tags": ["tag1", "tag2"]}
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_validate_failed(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{file_id}/tags',
        headers={'token': token},
        json={'tags': ['tag1', 'a'*33]}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    # 특수문자 사용 불가.
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{file_id}/tags',
        headers={'token': token},
        json={'tags': ['tag1', 'afv,ds']}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    

def test_success_create(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{file_id}/tags',
        headers={'token': token},
        json={"tags": ["tag1", "tag2"]}
    )
    
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json() == {
        'tags': [
            {'tag_name': 'tag1'},
            {'tag_name': 'tag2'},
        ]
    }

def test_success_modify(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{file_id}/tags',
        headers={'token': token},
        json={"tags": ["tag1", "tag5", "tag7"]}
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json() == {
        'tags': [
            {'tag_name': 'tag1'},
            {'tag_name': 'tag5'},
            {'tag_name': 'tag7'},
        ]
    }
