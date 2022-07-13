import pytest
import os
from fastapi.testclient import TestClient
from fastapi import status


from main import app
from system.bootloader import Bootloader
from apps.auth.utils.managers import AppAuthManager
from apps.user.utils.managers import UserCRUDManager
from settings.base import SERVER


admin_info = None
client_info = None
f1, f2 = None, None
created_dirs = dict()

f1_id = None

TEST_EXAMLE_ROOT = 'apps/storage/tests/example'

@pytest.fixture(scope='module')
def api():
    global admin_info
    global client_info
    global f1
    global f2
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
    user = UserCRUDManager().create(**admin_info)
    admin_info['id'] = user.id
    # Add Client
    client_info = {
        'email': 'seokbong61@gmail.com',
        'name': 'jeonghyun2',
        'passwd': 'passwd0123',
        'storage_size': 10,
    }
    user = UserCRUDManager().create(**client_info)
    client_info['id'] = user.id
    # Open files for testing
    f1 = open(f'{TEST_EXAMLE_ROOT}/hi.txt', 'rb')
    f2 = open(f'{TEST_EXAMLE_ROOT}/hi2.txt', 'rb')
    # Return test api
    yield TestClient(app)
    # Close all files
    f1.close()
    f2.close()
    # Remove All Data
    Bootloader.remove_storage()
    Bootloader.remove_database()

# TESTING COMMON
def test_no_token(api: TestClient):
    res = api.post(
        f'/api/users/{admin_info["id"]}/datas/0',
        files=[
            ('files', (f1.name, f1)), 
            ('files', (f2.name, f2))
        ]
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_client_try_other_storage(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/users/{admin_info["id"]}/datas/0',
        json={'dirname': 'mydir'},
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_request_nothing(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_admin_try_to_upload_no_user(api: TestClient):
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)

    # File
    res = api.post(
        f'/api/users/99999999999/datas/0',
        headers={'token': token},
        files=[
            ('files', (f1.name, f1)), 
            ('files', (f2.name, f2))
        ]
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND

    # Directory
    res = api.post(
        f'/api/users/99999999999/datas/0',
        headers={'token': token},
        json={'dirname': 'mydir'}
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_fileupload_in_no_exists_root(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)
    
    # File
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/999999999999999999',
        headers={'token': token},
        files=[
            ('files', (f1.name, f1)), 
            ('files', (f2.name, f2))
        ]
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND

    # Directory
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/999999999999999999',
        headers={'token': token},
        json={'dirname': 'mydir'}
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND

# TESTING DIRECTORY
def test_directory_validation(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)

    # / 사용 금지
    assert api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        json={'dirname': 'abce/sbc'}
    ).status_code == status.HTTP_400_BAD_REQUEST

    # \ 사용 금지
    assert api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        json={'dirname': 'abce\\sbc'}
    ).status_code == status.HTTP_400_BAD_REQUEST

    # : 사용 금지
    assert api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        json={'dirname': 'abce:sbc'}
    ).status_code == status.HTTP_400_BAD_REQUEST

    # * 사용 금지
    assert api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        json={'dirname': 'abce*sbc'}
    ).status_code == status.HTTP_400_BAD_REQUEST

    # " 사용 금지
    assert api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        json={'dirname': 'abce"sbc'}
    ).status_code == status.HTTP_400_BAD_REQUEST

    # ' 사용 금지
    assert api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        json={'dirname': "bce'sbc"}
    ).status_code == status.HTTP_400_BAD_REQUEST

    # < 사용 금지
    assert api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        json={'dirname': "bce<sbc"}
    ).status_code == status.HTTP_400_BAD_REQUEST

    # > 사용 금지
    assert api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        json={'dirname': "bce>sbc"}
    ).status_code == status.HTTP_400_BAD_REQUEST

    # | 사용 금지
    assert api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        json={'dirname': "bce|sbc"}
    ).status_code == status.HTTP_400_BAD_REQUEST

    # 비어있음
    assert api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        json={'dirname': ''}
    ).status_code == status.HTTP_400_BAD_REQUEST

def test_success_directory(api: TestClient):
    """
        생성 될 예정인 디렉토리
        mydir
            `-subdir
            `-mydir
    """
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)

    # 최상위의 mydir 생성
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        json={'dirname': 'mydir'}
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert len(res.json()) == 1
    main_mydir = res.json()[0]
    # Response Data 확인
    assert main_mydir == {
        'is_dir': True,
        'id': main_mydir['id'],
        'root': '/',
        'name': 'mydir',
        'created': main_mydir['created'],
    }
    # 제대로 디렉토리가 생성되어 있는 지 확인
    assert os.path.isdir(f'{SERVER["storage"]}/storage/{client_info["id"]}/root/mydir')

    # subdir 생성
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{main_mydir["id"]}',
        headers={'token': token},
        json={'dirname': 'subdir'}
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert len(res.json()) == 1
    sub_subdir = res.json()[0]
    # Response Data 확인
    assert sub_subdir == {
        'is_dir': True,
        'id': sub_subdir['id'],
        'root': '/mydir/',
        'name': 'subdir',
        'created': sub_subdir['created']
    }
    # 제대로 생성되어 있는 지 확인
    assert os.path.isdir(f'{SERVER["storage"]}/storage/{client_info["id"]}/root/mydir/subdir')

    created_dirs['mydir'] = main_mydir
    created_dirs['mydir/subdir'] = sub_subdir

def admin_can_create_to_other_storage(api: TestClient):
    # 관리자는 다른 계정에 디렉토리를 생성할 수 있다.
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    
    # sub의 mydir 생성
    # 같은 이름의 디렉토리라도 다른 위치면 생성이 가능하다
    main_mydir = created_dirs['mydir']
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{main_mydir["id"]}',
        headers={'token': token},
        json={'dirname': 'mydir'}
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert len(res.json()) == 1
    sub_mydir = res.json()[0]
    # Response Data 확인
    assert sub_mydir == {
        'is_dir': True,
        'id': sub_mydir['id'],
        'root': '/mydir/',
        'name': 'mydir',
        'created': sub_mydir['created']
    }
    # 제대로 생성되어 있는 지 확인
    assert os.path.isdir(f'{SERVER["storage"]}/storage/{client_info["id"]}/root/mydir/mydir')

def test_create_same_directory(api: TestClient):
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        json={'dirname': 'mydir'}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

# TESTING FILE
def test_file_upload(api: TestClient):
    global f1_id
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)

    # 메인 디렉토리 파일 업로드
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        files = [
            ('files', (f1.name, f1)), 
            ('files', (f2.name, f2))
        ]
    )
    assert res.status_code == status.HTTP_201_CREATED
    output = res.json()
    assert output == [
        {
            'is_dir': False,
            'id': output[0]['id'],
            'root': '/',
            'name': 'hi.txt',
            'created': output[0]['created']
        },
        {
            'is_dir': False,
            'id': output[1]['id'],
            'root': '/',
            'name': 'hi2.txt',
            'created': output[1]['created']
        }
    ]

    # 서브 디렉토리 파일 업로드 + 관리자가 특정 클라이언트의 스토리지에 업로드 가능
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{created_dirs["mydir"]["id"]}',
        headers={'token': token},
        files = [
            ('files', (f1.name, f1)), 
            ('files', (f2.name, f2))
        ]
    )
    assert res.status_code == status.HTTP_201_CREATED
    output = res.json()
    assert output == [
        {
            'is_dir': False,
            'id': output[0]['id'],
            'root': '/mydir/',
            'name': 'hi.txt',
            'created': output[0]['created']
        },
        {
            'is_dir': False,
            'id': output[1]['id'],
            'root': '/mydir/',
            'name': 'hi2.txt',
            'created': output[1]['created']
        }
    ]
    
    # 파일 생성 확인
    assert os.path.isfile(f'{SERVER["storage"]}/storage/{client_info["id"]}/root/mydir/hi.txt')
    assert os.path.isfile(f'{SERVER["storage"]}/storage/{client_info["id"]}/root/mydir/hi2.txt')

    f1_id = output[0]['id']

def test_rewrite_file(api: TestClient):
    # 같은 이릉의 파일 업로드일 경우, 덮어쓰기 가능
    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)

    # 메인 디렉토리 파일 업로드
    res = api.post(
        f'/api/users/{client_info["id"]}/datas/0',
        headers={'token': token},
        files = [
            ('files', (f1.name, f1)),
        ]
    )
    assert res.status_code == status.HTTP_201_CREATED

    # 파일 존재 확인
    assert os.path.isfile(f'{SERVER["storage"]}/storage/{client_info["id"]}/root/mydir/hi.txt')

def test_try_create_on_file(api: TestClient):
    # 파일위에 파일/디렉토리를 생성하는 것은 불가능
    # 디렉토리를 못찾은 걸로 간주

    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.post(
        f'/api/users/{client_info["id"]}/datas/{f1_id}',
        headers={'token': token},
        files = [('files', (f1.name, f1))]
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND
