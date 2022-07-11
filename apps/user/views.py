from typing import List
from fastapi import APIRouter, HTTPException, Request, status
import pydantic
import json

from apps.user.models import User
from apps.user.schemas import UserRead
from apps.user.utils.managers import UserManager
from core.exc import UserAlreadyExists, UserNotFound


user_router = APIRouter(
    prefix='/api/users',
    tags=['user'],
    responses={404: {'error': 'Not Found'}}
)
user_search_router = APIRouter(
    prefix='/api/users/search',
    tags=['user', 'search'],
    responses={404: {'error': 'Not Found'}}
)

class UserView:

    """
    (POST)  /api/user           # 생성
    (GET)   /api/user/{id}      # 유저 정보 가지고오기
    (PATCH) /api/user/{id}      # 유저 정보 업데이트하기
    (DELETE)/api/user/{id}      # 유저 삭제하기
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
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='요청 토큰이 없습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        
        try:
            # 요청 데이터 가져오기
            req = await request.json()
        except json.decoder.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='요청 데이터가 없습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')

        try:
            # 사용자 추가하기
            user: User = UserManager().create_user(token=token, **req)
        except TypeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='요청 데이터의 일부가 빠져있습니다.')
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='권한이 없습니다.')
        except pydantic.ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e))
        except UserAlreadyExists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='해당 정보를 가진 사용자가 이미 존재합니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        else:
            return user

    
    @staticmethod
    @user_router.get(
        path='/{pk}',
        status_code=status.HTTP_200_OK,
        response_model=UserRead)
    async def get_user(request: Request, pk: int):
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
            # 사용자 검색하기
            user: User = UserManager().read_user(token, pk)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='권한이 없습니다.')
        except UserNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='검색 대상의 사용자가 없습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        else:
            return user

    @staticmethod
    @user_router.patch(
        path='/{pk}',
        status_code=status.HTTP_200_OK,
        response_model=UserRead)
    async def update_user(request: Request, pk: int):
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
        except json.decoder.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='요청 데이터가 없습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')

        try:
            # 업데이트 하기
            user: User = UserManager() \
                .update_user(
                    token=token,
                    pk=pk, **req
                )
        except TypeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='요청 데이터의 일부가 빠져있습니다.')
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='권한이 없습니다.')
        except UserNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='없는 사용자 입니다.')
        except pydantic.ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        else:
            return user

    @staticmethod
    @user_router.delete(
        path='/{pk}',
        status_code=status.HTTP_204_NO_CONTENT)
    async def remove_user(request: Request, pk: int):
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
            # 유저 삭제하기
            UserManager().remove_user(token, pk)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='권한이 없습니다.')
        except UserNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='검색 대상의 사용자가 없습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')


class UserSearchView:
    """
    (GET)   /api/user/search    # 필터링으로 유저 검색하기
    """
    @staticmethod
    @user_search_router.get(
        path='',
        status_code=status.HTTP_200_OK,
        response_model=List[UserRead])
    async def search_users(request: Request):
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
            # 유저 데이터 가져오기
            queries = request.query_params._dict
            users: List[User] = \
                UserManager().search_users(token=token, **queries)
        except TypeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='요청 데이터의 일부가 빠졌습니다.')
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='권한이 없습니다.')
        except ValueError as e:
            # 검색 쿼리 Validation Error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        else:
            return users