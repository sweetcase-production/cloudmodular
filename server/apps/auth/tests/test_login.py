from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from core.init import init_app
from settings.base import DATABASE
from system.bootloader import Bootloader
from system.connection.generators import DatabaseGenerator


user_info = None

@pytest.fixture(scope='module')
def api():

    global user_info

    # Load Application
    DatabaseGenerator.load(db_type=DATABASE['type'], **DATABASE['data'])
    app: FastAPI = init_app()
    Bootloader.migrate_database()
    Bootloader.init_storage()

    # Add User
    user_info = {
        'email': 'seokbong60@gmail.com',
        'name': 'jeonhyun',
        'passwd': 'password0123',
        'storage_size': 5
    }

    from apps.user.utils.managers import UserCRUDManager
    UserCRUDManager().create(**user_info)

    yield TestClient(app)

    # Remove Application
    Bootloader.remove_storage()
    Bootloader.remove_database()

def test_success_get_login_token(api: TestClient):
    email, passwd = user_info['email'], user_info['passwd']
    print(email, passwd)