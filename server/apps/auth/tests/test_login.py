from fastapi import FastAPI
import pytest

from core.init import init_app

from system.bootloader import Bootloader



@pytest.fixture(scope='module')
def api():

    # Load Application
    app: FastAPI = init_app()
    Bootloader.migrate_database()
    Bootloader.init_storage()

    yield app

    # Remove Application
    Bootloader.remove_storage()
    Bootloader.remove_database()

