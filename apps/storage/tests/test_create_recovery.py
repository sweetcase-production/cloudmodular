import pytest
import os
import shutil
from fastapi.testclient import TestClient
from fastapi import UploadFile, status
from sqlalchemy import and_

from main import app
from apps.storage.models import DataInfo
from apps.auth.utils.managers import AppAuthManager
from apps.user.utils.managers import UserCRUDManager
from apps.storage.utils.managers import (
    DataFileCRUDManager,
    DataDirectoryCRUDManager,
)
from system.bootloader import Bootloader
from system.connection.generators import DatabaseGenerator
from settings.base import SERVER


admin_info = None
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

@pytest.fixture(scope='function')
def api():
    global admin_info
    global treedir
    global hi, hi2
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
    # Return test api
    yield TestClient(app)
    # Close all files and remove all data
    hi.close()
    hi2.close()
    Bootloader.remove_storage()
    Bootloader.remove_database()


def test_when_file_removed_illeagal_method(api: TestClient):
    """
    DB에 등록된 파일들 중에 일부가 스토리지에서 삭제됨
    이때 동일한 이름의 파일을 추가하게 된다면, 아무런 문제 없이 
    추가하여야 한다.
    """
    # mydir/hi.txt 삭제
    root = f'{SERVER["storage"]}/storage/{admin_info["id"]}/root/mydir/hi.txt'
    os.remove(root)
    assert not os.path.isfile(root)

    # Request
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/data/{admin_info["id"]}/{treedir["mydir"]["id"]}',
        headers={'token': token},
        files=[('files', (hi.name, hi))]
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert os.path.isfile(root)

def test_when_file_not_removed_data_in_db_removed(api: TestClient):
    """
    DB에는 없는데 스토리지에는 있는 파일들에 대한 테스트
    마찬가지로 덮어쓴다.
    """
    # mydir/second2.txt 추가
    root = f'{SERVER["storage"]}/storage/{admin_info["id"]}/root/mydir/second2.txt'
    with open(root, 'wt') as f:
        f.write('Why me?')
    assert os.path.isfile(root)

    # Request
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    with open(f'{TEST_EXAMLE_ROOT}/second2.txt', 'rb') as f:
        res = api.post(
            f'/api/data/{admin_info["id"]}/{treedir["mydir"]["id"]}',
            headers={'token': token},
            files=[('files', (f.name, f))]
        )
        assert res.status_code == status.HTTP_201_CREATED

    # DB에 저장되어 있는 지 확인
    session = DatabaseGenerator.get_session()
    assert session.query(DataInfo).filter(and_(
        DataInfo.root == '/mydir/',
        DataInfo.name == 'second2.txt',
        DataInfo.is_dir == False,
    )).scalar()

    # 데이터 변경 여부 확인
    with open(root, 'rb') as f1:
        with open(f'{TEST_EXAMLE_ROOT}/second2.txt', 'rb') as f2:
            assert f1.readline() == f2.readline()


def test_when_directory_removed_illeagal_method(api: TestClient):
    """
    디렉토리가 부적절한 방법으로 삭제되어 관련 DB데이터가 남아있는 경우
    파일 때와 마찬가지로 디렉토리만 생성해준다.
    그리고 디렉토리 안에 존재하는 모든 파일과 디렉토리는 DB 상에서 전부 지워져야 한다.
    """
    # mydir 삭제
    root = f'{SERVER["storage"]}/storage/{admin_info["id"]}/root/mydir'
    shutil.rmtree(root)
    assert not os.path.isdir(root)
    
    # Request
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/data/{admin_info["id"]}/0',
        headers={'token': token},
        json={'dirname': 'mydir'}
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert os.path.isdir(root)
    
    # DB에서 root하위의 데이터가 없어야 한다
    session = DatabaseGenerator.get_session()
    query = session.query(DataInfo)
    assert query.filter(DataInfo.root.startswith('/mydir/')).count() == 0


def test_when_directory_not_removed_but_db_removed(api: TestClient):
    """
    디렉토리는 스토리지에 존재하는데 DB에서 사라진 경우
    
    복구해주는 것이 베스트이지만, 아직 효율적인 방법을 찾지 못했으므로 전부 삭제한다.
    TODO: 복구 프로세스는 Alpha버전이 Release된 후에 진행할 예정이며
    TODO: 해당 복구 프로세스를 구현할 시, 해당 테스트코드를 전면 수정할 것
    """
    # mydir를 DB에서 삭제
    session = DatabaseGenerator.get_session()
    session.query(DataInfo).filter(and_(
        DataInfo.is_dir == True,
        DataInfo.root == '/',
        DataInfo.name == 'mydir',
    )).delete()
    session.commit()
    
    # Request
    email, passwd = admin_info['email'], admin_info['passwd']
    token = AppAuthManager().login(email, passwd)
    res = api.post(
        f'/api/data/{admin_info["id"]}/0',
        headers={'token': token},
        json={'dirname': 'mydir'}
    )
    assert res.status_code == status.HTTP_201_CREATED
    
    # DB에서 mydir하위의 정보는 전부 사라져야 한다.
    session = DatabaseGenerator.get_session()
    query = session.query(DataInfo)
    assert query.filter(DataInfo.root.startswith('/mydir/')).count() == 0
