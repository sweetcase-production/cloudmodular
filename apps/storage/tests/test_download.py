import pytest
from fastapi.testclient import TestClient
from fastapi import UploadFile, status

from main import app
from apps.auth.utils.managers import AppAuthManager
from system.bootloader import Bootloader
from apps.user.models import User
from apps.user.utils.managers import UserCRUDManager
from apps.storage.models import DataInfo
from apps.storage.utils.managers import (
    DataDirectoryCRUDManager,
    DataFileCRUDManager
)

client_info, admin_info, other_info = None, None, None
treedir = {
    'mydir': { 'id': None,
        'hi.txt': {'id': None, },
        'hi2.txt': {'id': None, },
        'subdir': {'id' : None,
            'hi.txt': {'id': None},
        }
    }
}
TEST_EXAMLE_ROOT = 'apps/storage/tests/example'

@pytest.fixture(scope="module")
def api():
    global client_info, admin_info, other_info
    # Load Application
    Bootloader.migrate_database()
    Bootloader.init_storage()
    # Add Client
    client_info = {
        'email': 'seokbong60@gmail.com',
        'name': 'jeonghyun',
        'passwd': 'passwd0123',
        'storage_size': 3,
    }
    user: User = UserCRUDManager().create(**client_info)
    client_info['id'] = user.id
    # Add Admin
    admin_info = {
        'email': 'napalosense@gmail.com',
        'name': 'admin',
        'passwd': 'passwd1234',
        'is_admin': True,
        'storage_size': 1,
    }
    user: User = UserCRUDManager().create(**admin_info)
    admin_info['id'] = user.id
    # Add Other User
    other_info = {
        'email': 'seokbong62@gmail.com',
        'name': 'jeonhyun3',
        'passwd': 'password0123',
        'storage_size': 5,
    }
    user = UserCRUDManager().create(**other_info)
    other_info['id'] = user.id
    # Upload Directory
    mydir: DataInfo = DataDirectoryCRUDManager().create(
        root_id=0, user_id=client_info['id'], dirname='mydir')
    treedir['mydir']['id'] = mydir.id
    subdir: DataInfo =DataDirectoryCRUDManager().create(
        root_id=mydir.id, user_id=client_info['id'], dirname='subdir')
    treedir['mydir']['subdir']['id'] = subdir.id
    # Upload Files in mydir
    for filename, file in (
        ("hi.txt", open(f'{TEST_EXAMLE_ROOT}/hi.txt', 'rb')),
        ("hi2.txt", open(f'{TEST_EXAMLE_ROOT}/hi2.txt', 'rb'))):
        res: DataInfo = DataFileCRUDManager().create(
            root_id=mydir.id, user_id=client_info['id'],
            file=UploadFile(filename=file.name, file=file))
        treedir['mydir'][filename]['id'] = res.id
    # Upload File in subdir
    with open(f'{TEST_EXAMLE_ROOT}/hi.txt', 'rb') as file:
        res: DataInfo = DataFileCRUDManager().create(
            root_id=subdir.id, user_id=client_info['id'],
            file=UploadFile(filename=file.name, file=file))
        treedir['mydir']['subdir']['hi.txt']['id'] = res.id
    # return API
    yield TestClient(app)
    # Close all files and remove all data
    Bootloader.remove_storage()
    Bootloader.remove_database()

def test_no_token(api: TestClient):
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/download',
        params={'ids': [treedir['mydir']['hi.txt']['id']]})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_other_access_failed(api: TestClient):
    email, passwd = other_info['email'], other_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/download',
        headers={'token': token},
        params={'ids': [treedir['mydir']['hi.txt']['id']]})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_user_not_found(api: TestClient):
    """
    해당 User를 찾지 못함
    """
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/99999999/datas/{treedir["mydir"]["id"]}/download',
        headers={'token': token},
        params={'ids': [treedir['mydir']['hi.txt']['id']]})
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_failed_directory_id(api: TestClient):
    """
    해당 디렉토리를 못찾음
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/99999999999/download',
        headers={'token': token},
        params={'ids': [treedir['mydir']['hi.txt']['id']]})
    assert res.status_code == status.HTTP_404_NOT_FOUND

    # 데이터는 존재하는 데 파일이면 불가능
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["hi.txt"]["id"]}/download',
        headers={'token': token},
        params={'ids': [treedir['mydir']['hi.txt']['id']]})
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_no_selected(api: TestClient):
    """
    아무것도 선택 안함
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/download',
        headers={'token': token},
        params={'ids': []})
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_file_not_found_when_single_download(api: TestClient):
    """
    단일 파일 다운로드 시 해당 파일이 존재하지 않는 경우
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/download',
        headers={'token': token},
        params={'ids': [9999999999]})
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_cannot_select_other_located_file(api: TestClient):
    """
    현재 위치에서 다른 위치의 데이터를 다운받을 수 없다.
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/download',
        headers={'token': token},
        params={'ids': [treedir['mydir']['subdir']['hi.txt']['id']]})
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_success_single_file_download(api: TestClient):
    """
    단일 파일 다운로드 성공
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/download',
        headers={'token': token},
        params={'ids': [treedir['mydir']['hi.txt']['id']]})
    assert res.status_code == status.HTTP_200_OK
    assert res.headers.get('content-type') == 'text/plain; charset=utf-8'

def test_success_single_directory_download(api: TestClient):
    """
    단일 디렉토리 다운로드 성공
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/download',
        headers={'token': token},
        params={'ids': [treedir['mydir']['subdir']['id']]})
    assert res.status_code == status.HTTP_200_OK
    assert res.headers.get('content-type') == 'application/zip'

def test_success_multiple_download(api: TestClient):
    """
    여러개 ZIP형식으로 다운로드 성공
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/download',
        headers={'token': token},
        params={'ids': [
                    treedir['mydir']['subdir']['id'],
                    treedir['mydir']['hi.txt']['id']]})
    assert res.status_code == status.HTTP_200_OK
    assert res.headers.get('content-type') == 'application/zip'

def test_try_multiple_but_allow_only_one_file(api: TestClient):
    """
    여러개 요청을 했으나 일부 ID는 정확하지 않아 하나만 다운로드
    이때 하나여도 ZIP형태로 다운받아야 한다.
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/download',
        headers={'token': token},
        params={'ids': [
                    999999999,
                    treedir['mydir']['hi.txt']['id']]})
    assert res.status_code == status.HTTP_200_OK
    assert res.headers.get('content-type') == 'application/zip'

def test_on_root(api: TestClient):
    """
    최상위 루트에서의 작동
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/0/download',
        headers={'token': token},
        params={'ids': [treedir['mydir']['id']]})
    assert res.status_code == status.HTTP_200_OK
    assert res.headers.get('content-type') == 'application/zip'

def test_no_one(api: TestClient):
    """
    아무것도 못찾음
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/download',
        headers={'token': token},
        params={'ids': [ 999999999, 99999997]})
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_admin_can_access_client(api: TestClient):
    """
    관리자는 남의 것도 다운 가능하다.
    동시애 Multiple Download로 인해 왕복한 파일들도 정상적으로 있는 지 테스트
    """
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/download',
        headers={'token': token},
        params={'ids': [
                    treedir['mydir']['subdir']['id'],
                    treedir['mydir']['hi.txt']['id']]})
    assert res.status_code == status.HTTP_200_OK
    assert res.headers.get('content-type') == 'application/zip'
