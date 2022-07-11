import datetime
import pytest
from unittest import TestCase as AssertFunc
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from system.bootloader import Bootloader
from apps.auth.utils.managers import AppAuthManager
from apps.user.utils.managers import UserCRUDManager
from apps.user.models import User

accounts = []

@pytest.fixture(scope='module')
def api():
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
    admin_info['created'] = admin.created
    
    accounts.append(admin_info)
    # 10개의 클라이언트 생성
    for k in range(10):
        req = {
            'email': f'seokbong60{k}@gmail.com',
            'name': f'jeonhyun{k}',
            'passwd': 'password0123',
            'storage_size': 5,
        }
        client = UserCRUDManager().create(**req)
        req['id'] = client.id
        req['is_admin'] = client.is_admin
        req['created'] = client.created
        accounts.append(req)
    # Return test api
    yield TestClient(app)
    # Remove All Of Data
    Bootloader.remove_storage()
    Bootloader.remove_database()

def test_no_token(api: TestClient):
    res = api.get('/api/users/search')
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_no_admin(api: TestClient):
    email, passwd = accounts[1]['email'], accounts[1]['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.get(
        '/api/users/search',
        params={'page_size': 3, 'page': 1}, headers={'Token': token})
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_without_paging(api: TestClient):
    email, passwd = accounts[0]['email'], accounts[0]['passwd']
    token = AppAuthManager().login(email, passwd)
    
    res = api.get('/api/users/search', headers={'Token': token})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    res = api.get(
        '/api/users/search', 
        params={'page_size': 1}, headers={'Token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    res = api.get(
        '/api/users/search', 
        params={'page': 1}, headers={'Token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_paging_validation(api: TestClient):
    email, passwd = accounts[0]['email'], accounts[0]['passwd']
    token = AppAuthManager().login(email, passwd)

    res = api.get(
        '/api/users/search',
        params={'page_size': 0, 'page': 1}, headers={'Token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    # page_size는 21이상 넘기지 못한다.
    res = api.get(
        '/api/users/search',
        params={'page_size': 21, 'page': 1}, headers={'Token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    res = api.get(
        '/api/users/search',
        params={'page_size': 10, 'page': 0}, headers={'Token': token}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_success(api: TestClient):
    email, passwd = accounts[0]['email'], accounts[0]['passwd']
    token = AppAuthManager().login(email, passwd)

    # 데이터 정리
    # 이름 오름차순으로 정렬
    answer = accounts.copy()
    answer.sort(key=lambda e: e['name'])
    for e in answer:
        e['created'] = e['created'].strftime('%Y-%m-%dT%H:%M:%S')
        del e['passwd']
    
    # 테스트 시작
    res = api.get(
        '/api/users/search',
        params={'page_size': 3, 'page': 1}, headers={'Token': token})
    assert res.status_code == status.HTTP_200_OK
    AssertFunc().assertCountEqual(res.json(), answer[3*0:3*1])

    res = api.get(
        '/api/users/search',
        params={'page_size': 3, 'page': 4}, headers={'Token': token})
    assert res.status_code == status.HTTP_200_OK
    AssertFunc().assertCountEqual(res.json(), answer[3*3:3*4])
