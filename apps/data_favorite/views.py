import json
from fastapi import APIRouter, HTTPException, Request, status

from apps.data_favorite.utils.managers import DataFavoriteManager
from core.exc import DataIsAlreadyFavorited, DataNotFound


data_favorite_router = APIRouter(
    prefix='/api/users/{user_id}/datas/favorites',
    tags=['storage', 'favorite'],
    responses={404: {'error': 'Not Found'}}
)

class DataFavoriteView:
    """
    (POST)      /api/users/{user_id}/datas/favorites                    즐겨찾기 추가
    (GET)       /api/users/{user_id}/datas/favorites?data_id=<int>      data_id상의 즐겨찾기된 데이터 갖고오기
    (DELETE)    /api/users/{user_id}/datas/favorites/<favorite_id:int>  즐겨찾기 해제
    """
    
    @staticmethod
    @data_favorite_router.post(
        path='',
        status_code=status.HTTP_201_CREATED)
    async def set_favorite(request: Request, user_id: int):
        data_id: int = None
        """
        즐겨찾기 설정
        post form(json)
        { "data_id": int }
        """
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
            # data_id 추출
            req = await request.json()
            data_id = req['data_id']
        except (RuntimeError, json.decoder.JSONDecodeError, KeyError):
            # json데이터 부정확함
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='즐겨찾기를 추가하고자 하는 파일 및 디렉토리가 선택되지 않았습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')

        try:
            # 즐겨찾기 추가
            DataFavoriteManager().set_favorite(token, user_id, data_id)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='권한이 없습니다.')
        except DataNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 파일 및 디렉토리가 없습니다.')
        except DataIsAlreadyFavorited:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='이미 즐겨찾기가 설정되었습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')

    @staticmethod
    @data_favorite_router.get(
        path='',
        status_code=status.HTTP_200_OK)
    async def get_favorite(request: Request, user_id: int):
        pass

    @staticmethod
    @data_favorite_router.delete(
        path='/{favorite_id}',
        status_code=status.HTTP_204_NO_CONTENT)
    async def unset_favorite(request: Request, user_id: int):
        pass
