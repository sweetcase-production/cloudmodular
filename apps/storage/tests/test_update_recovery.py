import shutil
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
    mydir = DataDirectoryCRUDManager().create(
        root_id=0, user_id=user['id'], dirname='mydir'
    )
    treedir['mydir']['id'] = mydir.id
    # add hi.txt, hi2.txt on mydir
    files = DataFileCRUDManager().create(
        root_id=mydir.id, user_id=user['id'],
        files=[
            UploadFile(filename=hi.name, file=hi),
            UploadFile(filename=hi2.name, file=hi2)
        ]
    )
    treedir['mydir']['hi.txt']['id'] = files[0].id
    treedir['mydir']['hi2.txt']['id'] = files[1].id
    # create subdir
    subdir = DataDirectoryCRUDManager().create(
        root_id=mydir.id, user_id=user['id'], dirname='subdir'
    )
    treedir['mydir']['subdir']['id'] = subdir.id
    # add hi.txt on subdir
    files = DataFileCRUDManager().create(
        root_id=subdir.id, user_id=user['id'],
        files=[UploadFile(filename=hi.name, file=hi)]
    )
    treedir['mydir']['subdir']['hi.txt']['id'] = files[0].id
    
    # release app
    yield TestClient(app)
    # Close and remove all data
    hi.close()
    hi2.close()
    Bootloader.remove_storage()
    Bootloader.remove_database()

def test_when_file_removed_illeagal_method(api: TestClient):
    """
    DB에 등록된 데이터 중 일부가 스토리지 상에서 삭제됨
    이때 DB상의 데이터도 같이 삭제한다.
    """
    root = f'{SERVER["storage"]}/storage/{client_info["id"]}/root/mydir/hi.txt'
    os.remove(root)
    assert not os.path.isfile(root)

    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.patch(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["hi.txt"]["id"]}',
        json={'name': 'others'},
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND
    with DatabaseGenerator.get_session() as session:
        assert not session.query(DataInfo) \
            .filter(DataInfo.id == treedir["mydir"]["hi.txt"]["id"]).scalar()


def test_when_directory_removed_illeagal_method(api: TestClient):
    """
    디렉토리가 DB엔 남아있고 스토리지 상에서 삭제된 경우
    정보를 죄다 삭제한다.
    """
    root = f'{SERVER["storage"]}/storage/{client_info["id"]}/root/mydir'
    shutil.rmtree(root)
    assert not os.path.isfile(root)

    email, passwd = client_info['email'], client_info['passwd']
    token = AppAuthManager().login(email, passwd)

    # 삭제된 디렉토리의 하위 파일 수정 시
    res = api.patch(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["hi.txt"]["id"]}',
        json={'name': 'others'},
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND
    with DatabaseGenerator.get_session() as session:
        assert not session.query(DataInfo) \
            .filter(DataInfo.id == treedir["mydir"]["hi.txt"]["id"]).scalar()
        session.close()

    # 디렉토리 수정 시
    res = api.patch(
        f'/api/users/{client_info["id"]}/datas/{treedir["mydir"]["id"]}',
        json={'name': 'others'},
        headers={'token': token}
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND
    with DatabaseGenerator.get_session() as session:
        assert 0 == session.query(DataInfo) \
            .filter(DataInfo.root.startswith('/mydir/')).count()
        session.close()
    