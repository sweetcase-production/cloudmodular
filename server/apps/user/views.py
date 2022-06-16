from fastapi import APIRouter, HTTPException, Request, status
import pydantic
from apps.user.models import User

from apps.user.schemas import UserRead
from apps.user.utils.managers import UserManager
from core.exc import UserAlreadyExists


user_router = APIRouter(
    prefix='/api/user',
    tags=['user'],
    responses={404: {'error': 'Not Found'}}
)

class UserView:

    """
    (POST)  /api/user           # 생성
    (GET)   /api/user/{name}    # 유저 정보 가지고오기
    (PATCH) /api/user/{name}    # 유저 정보 업데이트하기
    (DELETE)/api/user/{name}    # 유저 삭제하기
    """
    @staticmethod
    @user_router.post(
        path='',
        status_code=status.HTTP_201_CREATED,
        response_model=UserRead)
    async def create_user(request: Request):
        try:
            # 토큰 가져오기
            token = request.headers['token']
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='요청 토큰이 없습니다.')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        
        try:
            # 요청 데이터 가져오기
            req = await request.json()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='요청 데이터가 없습니다.')
        try:
            # 사용자 추가하기
            user: User = UserManager().create_user(token=token, **req)
        except TypeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='요청 데이터의 일부가 빠져있습니다.')
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='권한이 없습니다.')
        except pydantic.ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e))
        except UserAlreadyExists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='해당 정보를 가진 사용자가 이미 존재합니다.')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        else:
            return user

class UserSearchView:
    """
    (GET)   /api/user/search    # 필터링으로 유저 검색하기
    """
    pass