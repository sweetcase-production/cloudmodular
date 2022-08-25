import pytest
from fastapi.testclient import TestClient
from fastapi import UploadFile, status

from main import app
from apps.share.utils.queries import DataSharedQuery
from apps.user.utils.managers import UserCRUDManager
from apps.storage.utils.managers import (
    DataFileCRUDManager,
    DataDirectoryCRUDManager,
)
from system.bootloader import Bootloader


client_info, admin_info, other_info = None, None, None
other_info = None
hi, hi2 = None, None
"""
mydir과 mydir/hi.txt만 공유 설정
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

    # 공유 설정
    treedir['mydir']['shared_id'] \
        = DataSharedQuery().create(treedir['mydir']['id']).id
    treedir['mydir']['hi.txt']['shared_id'] \
        = DataSharedQuery().create(treedir['mydir']['hi.txt']['id']).id

    # Return test api
    yield TestClient(app)
    # Close all files and remove all data
    hi.close()
    hi2.close()
    Bootloader.remove_storage()
    Bootloader.remove_database()

def test_failed_shared_id(api: TestClient):
    res = api.get(f'/api/datas/shares/999999999/info')
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_shared_file(api: TestClient):
    res = api.get(f'/api/datas/shares/{treedir["mydir"]["hi.txt"]["shared_id"]}/info')
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == {
        'root': '/mydir/',
        'name': 'hi.txt',
        'is_dir': False,
    }

def test_shared_directory(api: TestClient):
    res = api.get(f'/api/datas/shares/{treedir["mydir"]["shared_id"]}/info')
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == {
        'root': '/',
        'name': 'mydir',
        'is_dir': True,
    }

def test_shared_not_found_by_not_active(api: TestClient):
    from apps.share.models import DataShared
    from system.bootloader import DatabaseGenerator
    # False 설정
    session = DatabaseGenerator.get_session()
    shared = session.query(DataShared) \
        .filter(DataShared.id == treedir["mydir"]["shared_id"]).scalar()
    shared.is_active = False
    session.commit()
    # 데이터 갖고오기 불가능
    res = api.get(f'/api/datas/shares/{treedir["mydir"]["shared_id"]}/info')
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_shared_expired(api: TestClient):
    from apps.share.models import DataShared
    from system.bootloader import DatabaseGenerator
    from datetime import datetime, timedelta
    # data를 1년전으로
    session = DatabaseGenerator.get_session()
    shared = session.query(DataShared) \
        .filter(DataShared.id == treedir["mydir"]["hi.txt"]["shared_id"]).scalar()
    shared.share_started = datetime.now() - timedelta(days=365)
    session.commit()
    # 불가능
    res = api.get(f'/api/datas/shares/{treedir["mydir"]["hi.txt"]["shared_id"]}/info')
    assert res.status_code == status.HTTP_404_NOT_FOUND