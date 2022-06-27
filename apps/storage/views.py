import json
import traceback
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, UploadFile, status
import pydantic
from apps.storage.models import DataInfo
from apps.storage.schemas import DataInfoRead

from apps.storage.utils.managers import DataManager
from core.exc import DataAlreadyExists, DataNotFound, UserNotFound


storage_router = APIRouter(
    prefix='/api/data',
    tags=['storage'],
    responses={404: {'error': 'Not Found'}}
)

class StorageView:

    """
    (POST)      /api/data/{user_id}/{data_id}   파일/디렉토리 생성
    (GET)       /api/data/{user_id}/{data_id}   파일/디렉토리 기본 정보
    (PATCH)     /api/data/{user_id}/{data_id}   파일/디렉토리 이름 수정
    (DELETE)    /api/data/{user_id}/{data_id}   파일/디렉토리 삭제
    """


    @staticmethod
    @storage_router.post(
        path='/{user_id}/{data_id}',
        status_code=status.HTTP_201_CREATED,
        response_model=List[DataInfoRead])
    async def create_data(
        request: Request, 
        user_id: int, 
        data_id: int, 
        files: Optional[List[UploadFile]] = None,
    ):
        try:
            # 토큰 가져오기
            token = request.headers['token']
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='요청 토큰이 없습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        
        dirname = None
        try:
            try:
                # 요청된 디렉토리 이름 추출하기
                _req = await request.json()
            except RuntimeError:
                # 없는 경우
                pass
            except Exception as e:
                # 알 수 없는 에러
                raise e
            else:    
                if _req and 'dirname' in _req:
                    dirname = _req['dirname']
        except json.decoder.JSONDecodeError:
            # 없는경우 그냥 패스한다.
            pass
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')

        if (not dirname) and (not files):
            # 디렉토리, 파일 요청 둘다 아무것도 없음
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='파일 업로드 또는 디렉토리 생성을 해야 합니다.')

        try:
            # 파일 업로드 또는 디렉토리 생성
            created_datas = DataManager().create(
                token, user_id,
                data_id, files, dirname
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='접근 권한이 없습니다.')
        except pydantic.ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e))
        except UserNotFound:
            """
            Admin이 Client에 데이터를 추가할 때
            해당 Client가 존재하지 않으면 발생하는 에러
            """
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='대상 유저를 찾을 수 없습니다.')
        except DataNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='파일 및 디렉토리를 생성하기 위한 상위 디렉토리가 없습니다.')
        except DataAlreadyExists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='해당 디렉토리가 이미 존재합니다.')
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        else:
            return created_datas

    @staticmethod
    @storage_router.get(
        path='/{user_id}/{data_id}',
        status_code=status.HTTP_200_OK)
    async def get_data_info(request: Request, user_id: int, data_id: int, method: str):
        
        res = {
            'root': None,
            'is_dir': None,
            'name': None,
            'size': None,
        }

        if method not in ('info', 'download'):
            # 잘못된 method값
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='잘못된 접근 입니다.')

        try:
            # 토큰 가져오기
            token = request.headers['token']
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='요청 토큰이 없습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')

        try:
            # 정보 검색
            data = DataManager().read(token, user_id, data_id)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='접근 권한이 없습니다.')
        except UserNotFound:
            """
            Admin이 Client에 데이터를 추가할 때
            해당 Client가 존재하지 않으면 발생하는 에러
            """
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='대상 유저를 찾을 수 없습니다.')
        except DataNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 데이터를 찾을 수 없습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')

        if method == 'info':
            return data['info']
        else:
            return data['file']

    @staticmethod
    @storage_router.patch(
        path='/{user_id}/{data_id}',
        status_code=status.HTTP_200_OK)
    async def update_data_info(request: Request, user_id: int, data_id: int):
        pass

    @staticmethod
    @storage_router.delete(
        path='/{user_id}/{data_id}',
        status_code=status.HTTP_200_OK)
    async def remove_data_info(request: Request, user_id: int, data_id: int):
        pass