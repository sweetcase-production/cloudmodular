import pytest
from fastapi.testclient import TestClient
from fastapi import UploadFile, status

from main import app
from apps.auth.utils.managers import AppAuthManager
from apps.user.utils.managers import UserCRUDManager
from apps.data_favorite.utils.query.data_favorite_query import DataFavoriteQuery
from apps.storage.utils.managers import (
    DataFileCRUDManager,
    DataDirectoryCRUDManager,
)
from system.bootloader import Bootloader


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
    # Make Directory and files
    """
    mydir
        `-hi.txt
        `-hi2.txt
        `-subdir
            `-hi.txt
    """
    hi = open(f'{TEST_EXAMLE_ROOT}/hi.txt', 'rb')
    hi2 = open(f'{TEST_EXAMLE_ROOT}/hi2.txt', 'rb')
    
    # add directory mydir on root
    mydir = DataDirectoryCRUDManager().create(
        root_id=0,
        user_id=user.id,
        dirname='mydir'
    )
    treedir['mydir']['id'] = mydir.id

    # add hi.txt, hi2.txt on mydir
    files = []
    for file in [hi, hi2]:
        files.append(DataFileCRUDManager().create(
            root_id=mydir.id, user_id=user.id,
            file=UploadFile(filename=file.name, file=file)))
    treedir['mydir']['hi.txt']['id'] = files[0].id
    treedir['mydir']['hi2.txt']['id'] = files[1].id
    # add subdir on mydir
    subdir = DataDirectoryCRUDManager().create(
        root_id=mydir.id, user_id=user.id, dirname='subdir')
    treedir['mydir']['subdir']['id'] = subdir.id
    # add hi.txt on subdir
    hi.close()
    hi = open(f'{TEST_EXAMLE_ROOT}/hi.txt', 'rb')
    files = DataFileCRUDManager().create(
        root_id=subdir.id,
        user_id=user.id,
        file=UploadFile(filename=hi.name, file=hi))
    treedir['mydir']['subdir']['hi.txt']['id'] = files.id

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

    # Set Favorite
    # mydir, mydir/hi.txt
    DataFavoriteQuery().update(client_info['id'], treedir['mydir']['id'], True)
    DataFavoriteQuery().update(client_info['id'], treedir['mydir']['hi.txt']['id'], True)

    # Return test api
    yield TestClient(app)
    # Close all files and remove all data
    hi.close()
    hi2.close()
    Bootloader.remove_storage()
    Bootloader.remove_database()

def test_no_token(api: TestClient):
    """
    토큰 없음
    """
    res = api.delete(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/favorites',
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_other_access_failed(api: TestClient):
    """
    관리자를 제외한 다른 사람은 접근할 수 없다.
    """
    email, passwd = other_info['email'], other_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.delete(
        f'/api/users/{client_info["id"]}/datas/1/favorites',
        headers={'token': token},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_data_no_exists(api: TestClient):
    """
    대상 데이터가 애초에 존재하지 않는다.
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.delete(
        f'/api/users/{client_info["id"]}/datas/9999999/favorites',
        headers={'token': token},
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_try_unseted_data(api: TestClient):
    """
    설정 해제된 데이터를 또 다시 시도할 수는 없다.
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.delete(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["subdir"]["id"]}/favorites',
        headers={'token': token},
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_success(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.delete(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}/favorites',
        headers={'token': token},
    )
    assert res.status_code == status.HTTP_204_NO_CONTENT

    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.delete(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["hi.txt"]["id"]}/favorites',
        headers={'token': token},
    )
    assert res.status_code == status.HTTP_204_NO_CONTENT
