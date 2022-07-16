


from typing import Optional
from fastapi import APIRouter, Request, status


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
        data_id: int,
        recursive: bool = False,
        users: Optional[str] = None,
        favorite: bool = False,
        shared: bool = False,
        sort_create: bool = False,
        sort_name: bool  = False,
    ):
        pass