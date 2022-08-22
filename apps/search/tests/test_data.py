import pytest
from fastapi.testclient import TestClient
from fastapi import UploadFile, status

from main import app
from apps.data_favorite.utils.query.data_favorite_query import DataFavoriteQuery
from apps.share.utils.queries import DataSharedQuery
from apps.auth.utils.managers import AppAuthManager
from apps.user.utils.managers import UserCRUDManager
from apps.storage.utils.managers import (
    DataFileCRUDManager,
    DataDirectoryCRUDManager,
)
from system.bootloader import Bootloader
from apps.data_tag.utils.queries import DataTagQuery


client_info, admin_info, other_info = None, None, None
other_info = None
hi, hi2 = None, None
"""
mydir과 mydir/hi.txt만 공유 설정
mydir/hi.txt와 mydir/subdir에 즐겨찾기 설정
"""
treedir = {
    'mydir': {
        'id': None, 'shared_id': None,
        'hi.txt': {'id': None, 'shared_id': None},
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
    files = DataFileCRUDManager().create(
        root_id=mydir.id,
        user_id=user.id,
        files=[
            UploadFile(filename=hi.name, file=hi),
            UploadFile(filename=hi2.name, file=hi2)
        ]
    )
    treedir['mydir']['hi.txt']['id'] = files[0].id
    treedir['mydir']['hi2.txt']['id'] = files[1].id
    # add subdir on mydir
    subdir = DataDirectoryCRUDManager().create(
        root_id=mydir.id,
        user_id=user.id,
        dirname='subdir'
    )
    treedir['mydir']['subdir']['id'] = subdir.id
    # add hi.txt on subdir
    files = DataFileCRUDManager().create(
        root_id=subdir.id,
        user_id=user.id,
        files=[
            UploadFile(filename=hi.name, file=hi),
        ]
    )
    treedir['mydir']['subdir']['hi.txt']['id'] = files[0].id

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

    # 공유 설정
    treedir['mydir']['shared_id'] \
        = DataSharedQuery().create(treedir['mydir']['id']).id
    treedir['mydir']['hi.txt']['shared_id'] \
        = DataSharedQuery().create(treedir['mydir']['hi.txt']['id']).id

    # 즐겨찾기 설정
    DataFavoriteQuery() \
        .update(client_info['id'], treedir['mydir']['hi.txt']['id'], True)
    DataFavoriteQuery() \
        .update(client_info['id'], treedir['mydir']['subdir']['id'], True)

    # 태그 달기
    DataTagQuery().create(
        data_id=treedir['mydir']['subdir']['id'], tags=['tag1']
    )
    DataTagQuery().create(
        data_id=treedir['mydir']['hi.txt']['id'], tags=['tag1', 'tag2']
    )

    # Return test api
    yield TestClient(app)
    # Close all files and remove all data
    hi.close()
    hi2.close()
    Bootloader.remove_storage()
    Bootloader.remove_database()


def test_no_token(api: TestClient):
    res = api.get(
        '/api/search/datas', 
        params={'root': '/', 'user': client_info['name']}
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_target_user_not_exists(api: TestClient):
    # 없는 User는 비어있는 상태로 리턴
    email, passwd = admin_info["email"], admin_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',  params={'root': '/', 'user': 'adkfjlsd'},
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == []

def test_client_access_others_data(api: TestClient):
    email, passwd = other_info["email"], other_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={'root': '/mydir', 'user': client_info['name']},
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    
    # 전체 탐색
    res = api.get(
        '/api/search/datas',
        params={'root': '/', 'user': client_info['name']},
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_omit_root(api: TestClient):
    email, passwd = client_info["email"], client_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={
            'user': client_info['name'], 
            'sort_name': 1
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_search_wrong_root_id(api: TestClient):
    email, passwd = client_info["email"], client_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={
            'root_id': 99999999,
            'user': client_info['name'], 
            'sort_name': 1
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == []

def test_search_root_but_it_is_file(api: TestClient):
    # 파일이 디렉토리 취급을 받진 않는다.
    email, passwd = client_info["email"], client_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={
            'root_id': treedir['mydir']['hi.txt']['id'],
            'user': client_info['name'], 
            'sort_name': 1
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == []

def test_all_search_on_current_root(api: TestClient):
    # 현재 위치에서의 파일/디렉토리만 검색
    email, passwd = client_info["email"], client_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={
            'root': '/', 
            'user': client_info['name'], 
            'sort_name': 1
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    outputs = res.json()
    for output in outputs:
        # 날짜 데이터만 있는지 확인하고 실제 검토 X
        del output['created']
    # 2022-01-01T24:24:24
    assert outputs == [
        {
            
            'id': treedir['mydir']['id'],
            'root': '/',
            'is_dir': True,
            'name': 'mydir',
            'is_favorite': False,
            'shared_id': treedir['mydir']['shared_id'],
        }
    ]

def test_all_search_on_subdir_root(api: TestClient):
    # subdir위치에서의 파일 디렉토리 검색
    email, passwd = admin_info["email"], admin_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={
            'root': '/mydir/subdir/', 
            'user': client_info['name'], 
            'sort_name': 1
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    outputs = res.json()
    for output in outputs:
        # 날짜 데이터만 있는지 확인하고 실제 검토 X
        del output['created']
    assert outputs == [
        {
            
            'id': treedir['mydir']['subdir']['hi.txt']['id'],
            'root': '/mydir/subdir/',
            'is_dir': False,
            'name': 'hi.txt',
            'is_favorite': False,
            'shared_id': -1,
        }
    ]

def test_all_search_on_subdir_root_by_root_id(api: TestClient):
    # subdir위치에서의 파일 디렉토리 검색
    email, passwd = admin_info["email"], admin_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={
            'root_id': treedir['mydir']['subdir']['id'], 
            'user': client_info['name'], 
            'sort_name': 1
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    outputs = res.json()
    for output in outputs:
        # 날짜 데이터만 있는지 확인하고 실제 검토 X
        del output['created']
    assert outputs == [
        {
            'id': treedir['mydir']['subdir']['hi.txt']['id'],
            'root': '/mydir/subdir/',
            'is_dir': False,
            'name': 'hi.txt',
            'is_favorite': False,
            'shared_id': -1,
        }
    ]


def test_all_search_by_recursive(api: TestClient):
    # 전체검색 + 하위 데이터까지 모조리 다
    email, passwd = client_info["email"], client_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={
            'root': '/', 
            'user': client_info['name'],
            'recursive': 1,
            'sort_name': 1,
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    outputs = res.json()
    for output in outputs:
        # 날짜 데이터만 있는지 확인하고 실제 검토 X
        del output['created']
    assert outputs == [
        {
            'id': treedir['mydir']['id'],
            'root': '/',
            'is_dir': True,
            'name': 'mydir',
            'is_favorite': False,
            'shared_id': treedir['mydir']['shared_id'],
        },
        {
            'id': treedir['mydir']['subdir']['id'],
            'root': '/mydir/',
            'is_dir': True,
            'name': 'subdir',
            'is_favorite': True,
            'shared_id': -1,
        },
        {
            'id': treedir['mydir']['hi.txt']['id'],
            'root': '/mydir/',
            'is_dir': False,
            'name': 'hi.txt',
            'is_favorite': True,
            'shared_id': treedir['mydir']['hi.txt']['shared_id'],
        },
        {
            'id': treedir['mydir']['subdir']['hi.txt']['id'],
            'root': '/mydir/subdir/',
            'is_dir': False,
            'name': 'hi.txt',
            'is_favorite': False,
            'shared_id': -1,
        },
        {
            'id': treedir['mydir']['hi2.txt']['id'],
            'root': '/mydir/',
            'is_dir': False,
            'name': 'hi2.txt',
            'is_favorite': False,
            'shared_id': -1,
        },
    ]

def test_all_by_recursive_in_root_id(api: TestClient):
    # 전체검색 + 하위 데이터까지 모조리 다
    email, passwd = client_info["email"], client_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={
            'root_id': 0, 
            'user': client_info['name'],
            'recursive': 1,
            'sort_name': 1,
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    outputs = res.json()
    for output in outputs:
        # 날짜 데이터만 있는지 확인하고 실제 검토 X
        del output['created']
    assert outputs == [
        {
            'id': treedir['mydir']['id'],
            'root': '/',
            'is_dir': True,
            'name': 'mydir',
            'is_favorite': False,
            'shared_id': treedir['mydir']['shared_id'],
        },
        {
            'id': treedir['mydir']['subdir']['id'],
            'root': '/mydir/',
            'is_dir': True,
            'name': 'subdir',
            'is_favorite': True,
            'shared_id': -1,
        },
        {
            'id': treedir['mydir']['hi.txt']['id'],
            'root': '/mydir/',
            'is_dir': False,
            'name': 'hi.txt',
            'is_favorite': True,
            'shared_id': treedir['mydir']['hi.txt']['shared_id'],
        },
        {
            'id': treedir['mydir']['subdir']['hi.txt']['id'],
            'root': '/mydir/subdir/',
            'is_dir': False,
            'name': 'hi.txt',
            'is_favorite': False,
            'shared_id': -1,
        },
        {
            'id': treedir['mydir']['hi2.txt']['id'],
            'root': '/mydir/',
            'is_dir': False,
            'name': 'hi2.txt',
            'is_favorite': False,
            'shared_id': -1,
        },
    ]


def test_search_shared(api: TestClient):
    # 공유된 데이터만.
    email, passwd = client_info["email"], client_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={
            'root': '/', 
            'user': client_info['name'],
            'recursive': 1,
            'sort_name': 1,
            'shared': 1,
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    outputs = res.json()
    for output in outputs:
        # 날짜 데이터만 있는지 확인하고 실제 검토 X
        del output['created']
    assert outputs == [
        {
            'id': treedir['mydir']['id'],
            'root': '/',
            'is_dir': True,
            'name': 'mydir',
            'is_favorite': False,
            'shared_id': treedir['mydir']['shared_id'],
        },
        {
            'id': treedir['mydir']['hi.txt']['id'],
            'root': '/mydir/',
            'is_dir': False,
            'name': 'hi.txt',
            'is_favorite': True,
            'shared_id': treedir['mydir']['hi.txt']['shared_id'],
        },
    ]

def test_search_by_favorite(api: TestClient):

    email, passwd = client_info["email"], client_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={
            'root': '/', 
            'user': client_info['name'],
            'recursive': 1,
            'sort_name': 1,
            'favorite': 1,
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    outputs = res.json()
    for output in outputs:
        # 날짜 데이터만 있는지 확인하고 실제 검토 X
        del output['created']
    assert outputs == [
        {
            'id': treedir['mydir']['subdir']['id'],
            'root': '/mydir/',
            'is_dir': True,
            'name': 'subdir',
            'is_favorite': True,
            'shared_id': -1,
        },
        {
            'id': treedir['mydir']['hi.txt']['id'],
            'root': '/mydir/',
            'is_dir': False,
            'name': 'hi.txt',
            'is_favorite': True,
            'shared_id': treedir['mydir']['hi.txt']['shared_id'],
        }
    ]

def test_certain_word(api: TestClient):
    email, passwd = client_info["email"], client_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={
            'root': '/', 
            'user': client_info['name'],
            'recursive': 1,
            'sort_name': 1,
            'word': 'txt',
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    outputs = res.json()
    for output in outputs:
        # 날짜 데이터만 있는지 확인하고 실제 검토 X
        del output['created']
    assert outputs == [
        {
            'id': treedir['mydir']['hi.txt']['id'],
            'root': '/mydir/',
            'is_dir': False,
            'name': 'hi.txt',
            'is_favorite': True,
            'shared_id': treedir['mydir']['hi.txt']['shared_id'],
        },
        {
            'id': treedir['mydir']['subdir']['hi.txt']['id'],
            'root': '/mydir/subdir/',
            'is_dir': False,
            'name': 'hi.txt',
            'is_favorite': False,
            'shared_id': -1,
        },
        {
            'id': treedir['mydir']['hi2.txt']['id'],
            'root': '/mydir/',
            'is_dir': False,
            'name': 'hi2.txt',
            'is_favorite': False,
            'shared_id': -1,
        },
    ]

def test_tags(api: TestClient):
    email, passwd = client_info["email"], client_info["passwd"]
    token = AppAuthManager().login(email, passwd)
    res = api.get(
        '/api/search/datas',
        params={
            'root': '/', 
            'user': client_info['name'],
            'recursive': 1,
            'sort_name': 1,
            'tags': 'tag1,tag2'
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    outputs = res.json()
    for output in outputs:
        # 날짜 데이터만 있는지 확인하고 실제 검토 X
        del output['created']
    assert outputs == [
        {
            'id': treedir['mydir']['subdir']['id'],
            'root': '/mydir/',
            'is_dir': True,
            'name': 'subdir',
            'is_favorite': True,
            'shared_id': -1,
        },
        {
            'id': treedir['mydir']['hi.txt']['id'],
            'root': '/mydir/',
            'is_dir': False,
            'name': 'hi.txt',
            'is_favorite': True,
            'shared_id': treedir['mydir']['hi.txt']['shared_id'],
        },
    ]
    
    res = api.get(
        '/api/search/datas',
        params={
            'root': '/', 
            'user': client_info['name'],
            'recursive': 1,
            'sort_name': 1,
            'tags': 'tag2'
        },
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_200_OK
    outputs = res.json()
    for output in outputs:
        # 날짜 데이터만 있는지 확인하고 실제 검토 X
        del output['created']
    assert outputs == [
        {
            'id': treedir['mydir']['hi.txt']['id'],
            'root': '/mydir/',
            'is_dir': False,
            'name': 'hi.txt',
            'is_favorite': True,
            'shared_id': treedir['mydir']['hi.txt']['shared_id'],
        },
    ]
