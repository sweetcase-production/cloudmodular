from fastapi import UploadFile, status
from fastapi.testclient import TestClient
import pytest
import os

from main import app
from settings.base import SERVER
from system.bootloader import Bootloader
from apps.user.utils.managers import UserCRUDManager
from apps.auth.utils.managers import AppAuthManager
from apps.storage.utils.managers import (
    DataDirectoryCRUDManager, 
    DataFileCRUDManager
)
from system.connection.generators import DatabaseGenerator
from apps.storage.models import DataInfo


client_info, admin_info, other_info = None, None, None
other_info = None
hi, hi2 = None, None
treedir = {
    'mydir': {
        'id': None,
        'hi.txt': {'id': None},
        'hi2.txt': {'id': None},
        'subdir': {
            'id': None,
            'hi.txt': {'id': None},
        }
    }
}
TEST_EXAMLE_ROOT = 'apps/storage/tests/example'

@pytest.fixture(scope='module')
def api():
    global client_info, admin_info, other_info
    global treedir
    global hi, hi2

    # Load Application
    Bootloader.migrate_database()
    Bootloader.init_storage()

    # Add Client
    client_info = {
        'email': 'seokbong60@gmail.com',
        'name': 'jeonhyun',
        'passwd': 'password0123',
        'storage_size': 5,
    }
    user = UserCRUDManager().create(**client_info)
    client_info['id'] = user.id
    # Add Admin
    admin_info = {
        'email': 'seokbong61@gmail.com',
        'name': 'jeonhyun2',
        'passwd': 'password0123',
        'storage_size': 5,
        'is_admin': True,
    }
    user = UserCRUDManager().create(**admin_info)
    admin_info['id'] = user.id
    # Add Other
    other_info = {
        'email': 'seokbong62@gmail.com',
        'name': 'jeonhyun3',
        'passwd': 'password0123',
        'storage_size': 5,
    }
    user = UserCRUDManager().create(**other_info)
    other_info['id'] = user.id

    # Add Directory/File on Client Storage
    """
    mydir
        `-hi.txt
        `-hi2.txt
        `-subdir
            `-hi.txt
    """
    hi = open(f'{TEST_EXAMLE_ROOT}/hi.txt', 'rb')
    hi2 = open(f'{TEST_EXAMLE_ROOT}/hi2.txt', 'rb')

    user = client_info  # add directory/files in client

    # add directory mydir on root
    mydir = DataDirectoryCRUDManager().create(
        root_id=0,
        user_id=user['id'],
        dirname='mydir'
    )
    treedir['mydir']['id'] = mydir.id
    # add hi.txt, hi2.txt on mydir
    files = []
    for file in [hi, hi2]:
        files.append(DataFileCRUDManager().create(
            root_id=mydir.id, user_id=user['id'],
            file=UploadFile(filename=file.name, file=file)))
    treedir['mydir']['hi.txt']['id'] = files[0].id
    treedir['mydir']['hi2.txt']['id'] = files[1].id
    # add subdir on mydir
    subdir = DataDirectoryCRUDManager().create(
        root_id=mydir.id, user_id=user['id'], dirname='subdir')
    treedir['mydir']['subdir']['id'] = subdir.id
    # add hi.txt on subdir
    hi.close()
    hi = open(f'{TEST_EXAMLE_ROOT}/hi.txt', 'rb')
    files = DataFileCRUDManager().create(
        root_id=subdir.id,
        user_id=user['id'],
        file=UploadFile(filename=hi.name, file=hi))
    treedir['mydir']['subdir']['hi.txt']['id'] = files.id

    
    # release app
    yield TestClient(app)
    # Close and remove all data
    hi.close()
    hi2.close()
    Bootloader.remove_storage()
    Bootloader.remove_database()

def test_no_token(api: TestClient):
    """
    토큰 없음
    """
    res = api.delete(f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_other_access_failed(api: TestClient):
    """
    다른 계정에 접근 시도
    """
    email, passwd = other_info['email'], other_info['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.delete(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}',
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_data_not_found(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.delete(
        f'/api/users/{client_info["id"]}/datas/99999999999999',
        headers={'token': token},
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_success_remove_file(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.delete(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["hi.txt"]["id"]}',
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_204_NO_CONTENT

    # 삭제 여부 확인
    assert not os.path.isfile(
        f'{SERVER["storage"]}/storage/{client_info["id"]}/root/mydir/hi.txt'
    )

def test_success_remove_directory(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.delete(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}',
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_204_NO_CONTENT
    # 삭제 여부 확인
    assert not os.path.isdir(
        f'{SERVER["storage"]}/storage/{client_info["id"]}/root/mydir'
    )
    with DatabaseGenerator.get_session() as session:
        query = session.query(DataInfo)
        assert query.filter(DataInfo.root.startswith('/mydir/')).count() == 0
        assert query.filter(DataInfo.name == 'mydir').count() == 0

