from dotenv import load_dotenv
load_dotenv()

from system.connection.generators import DatabaseGenerator

from fastapi import FastAPI
import uvicorn
import argparse

from settings.base import *
from system.bootloader import Bootloader

# Engines
DatabaseGenerator.load(db_type=DATABASE['type'], **DATABASE['data'])

from core.init import init_app
app: FastAPI = init_app()

if __name__ == '__main__':
    """
    COMMAND LIST
    
    run-app: running app
        - dev: For Development
        - prod: For Deploy
    migrate: migrate database
        - dev: For Development
        - prod: For Deploy
    clean: remove ALL Data of database and storage
    """

    # Parser 생성
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--method', 
        metavar='method', 
        type=str, 
        help='Operation of running app',
        choices=['run-app', 'migrate', 'clean'],
        required=True
    )
    parser.add_argument(
        '--type', 
        metavar='type', 
        type=str, 
        help='Type of running app',
        choices=['dev', 'prod'],
        required=True,
    )
    args = parser.parse_args()

    # 분기 실행
    if args.method == 'run-app':
        # APP 실행
        """
        TODO:
        Admin이 있는 지 확인한 다음, 없으면 새로 생성한다.
        """
        if args.type == 'dev':
            uvicorn.run(app, host='0.0.0.0', port=SERVER['port'])
        elif args.type == 'prod':
            uvicorn.run(app, host='0.0.0.0', port=SERVER['port'])
    elif args.method == 'migrate':
        # Database, Storage Migration
        if args.type == 'dev':
            Bootloader.migrate_database()
            Bootloader.init_storage()
        elif args.type == 'prod':
            Bootloader.migrate_database()
            Bootloader.init_storage()
    elif args.method == 'clean':
        # 데이터 전부 삭제
        if args.type == 'prod':
            Bootloader.remove_storage()
            Bootloader.remove_database()
        elif args.type == 'dev':
            Bootloader.remove_storage()
            Bootloader.remove_database()
