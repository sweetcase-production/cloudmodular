from typing import Optional
from fastapi import APIRouter, HTTPException, Request, status

from apps.search.managers import DataSearchManager


search_router = APIRouter(
    prefix='/api/search',
    tags=['search'],
    responses={404: {'error': 'Not Found'}}
)

class SearchView:

    @staticmethod
    @search_router.get(
        path='/datas',
        status_code=status.HTTP_200_OK)
    def search_datas(
        request: Request,
        user: str,                      # 사용자 이름
        root: Optional[str] = None,     # 탐색 위치(디렉토리만)
        root_id: Optional[int] = None,  # 탐색 위치(디렉토리 아이디)
        recursive: int = 0,             # 하위 부분까지 전부 탐색
        favorite: int = 0,              # 즐겨찾기 여부
        shared: int = 0,                # 공유 여부
        tags: Optional[str] = None,     # 태그가 포함된 데이터만
        word: Optional[str] = None,     # 연관검색어
        sort_create: int = 0,           # 생성 순 정렬
        sort_name: int = 0,             # 이름 순 정렬
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
            return DataSearchManager().search(
                token, user, root, root_id, recursive, favorite,
                shared, tags, word, sort_create, sort_name
            )
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='권한이 없습니다.')
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='올바르지 않은 요청 입니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
