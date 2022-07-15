

import json
from fastapi import APIRouter, HTTPException, Request, status

from apps.data_tag.utils.managers import DataTagManager
from core.exc import DataNotFound, UserNotFound

data_tag_router = APIRouter(
    prefix='/api/users/{user_id}/datas/{data_id}/tags',
    tags=['storage', 'tag'],
    responses={404: {'error': 'Not Found'}}
)

class DataTagView:

    """
    (POST)  /api/users/{user_id}/datas/{data_id}/tags   파일에 대한 태그 갱신(추가/수정/삭제 동시에 작동)
    (GET)   /api/users/{user_id}/datas/{data_id}/tags   해당 파일/디렉토리에 대한 태그 가져오기
    """

    @staticmethod
    @data_tag_router.post(
        path='',
        status_code=status.HTTP_201_CREATED)
    async def create_tag_on_data(
        request: Request, 
        user_id: int,
        data_id: int
    ):
        try:
            # 토큰 가져오기
            token = request.headers['token']
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='요청 토큰이 없습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')

        try:
            # 요청 데이터 가져오기
            req = await request.json()
            tags = req['tags']
        except (json.decoder.JSONDecodeError, RuntimeError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='요청 데이터가 없습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')

        try:
            # 태그 갱신
            res_tags = DataTagManager() \
                .create_tags(token, user_id, data_id, tags)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='권한이 없습니다.')
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='적용할 수 없는 태그 이름이 포함되어 있습니다.')
        except DataNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 파일 및 디렉토리가 없습니다.')
        except UserNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 유저는 존재하지 않습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        else:
            return {'tags': res_tags}

    @staticmethod
    @data_tag_router.get(
        path='',
        status_code=status.HTTP_200_OK)
    async def get_tags_from_data(
        request: Request, 
        user_id: int, 
        data_id: int
    ):
        try:
            # 토큰 가져오기
            token = request.headers['token']
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='요청 토큰이 없습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')

        try:
            res = DataTagManager().get_tag_from_data(token, user_id, data_id)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='권한이 없습니다.')
        except DataNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 파일 및 디렉토리가 없습니다.')
        except UserNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 유저는 존재하지 않습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        else:
            return {'tags': res}
