from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import FileResponse

from apps.share.utils.managers import DataSharedManager
from core.exc import DataIsAlreadyShared, DataIsNotShared, DataNotFound, UserNotFound
from core.background_tasks import background_remove_file

data_shared_router = APIRouter(
    prefix='/api/users/{user_id}/datas/{data_id}/shares',
    tags=['storage', 'share'],
    responses={404: {'error': 'Not Found'}}
)

data_shared_download_router = APIRouter(
    prefix='/api/datas/shares/{shared_id}',
    tags=['storage', 'share'],
    responses={404: {'error': 'Not Found'}}
)

class DataSharedView:
    """
    (POST)      /api/users/<user_id:int>/datas/{data_id}/shares 공유 설정
    (GET)       /api/users/<user_id:int>/datas/{data_id}/shares 공유 URL 받아오기
    (DELETE)    /api/users/<user_id:int>/datas/{data_id}/shares 공유 해제
    """

    @staticmethod
    @data_shared_router.post(
        path='',
        status_code=status.HTTP_201_CREATED)
    def set_shared(
        request: Request,
        user_id: int,
        data_id: int,
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
            # 공유 설정
            shared_id = DataSharedManager().set_data_shared(token, user_id, data_id)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='접근 권한이 없습니다.')
        except UserNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 유저가 없습니다.')
        except DataNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 파일 및 디렉토리가 없습니다.')
        except DataIsAlreadyShared:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='이미 공유 되었습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        else:
            return {'shared_id': shared_id}

    @staticmethod
    @data_shared_router.get(
        path='',
        status_code=status.HTTP_200_OK)
    def get_shared(
        request: Request,
        user_id: int,
        data_id: int,
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
            # 공유 설정
            shared_id = DataSharedManager().get_shared_id(token, user_id, data_id)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='접근 권한이 없습니다.')
        except UserNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 유저가 없습니다.')
        except DataNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 파일 및 디렉토리가 없습니다.')
        except DataIsNotShared:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='이미 공유 되었습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        else:
            return {'shared_id': shared_id}

    @staticmethod
    @data_shared_router.delete(
        path='',
        status_code=status.HTTP_204_NO_CONTENT)
    def unset_shared(
        request: Request,
        user_id: int,
        data_id: int,
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
            DataSharedManager().unset_data_shared(token, user_id, data_id)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='접근 권한이 없습니다.')
        except UserNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 유저가 없습니다.')
        except DataNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 파일 및 디렉토리가 없습니다.')
        except DataIsNotShared:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='공유가 되어 있지 않습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')

class DataSharedDataDownloadView:
    """
    (GET)   /api/datas/shares/<shared_id:int>/download  공유 데이터 다운로드
    (GET)   /api/datas/shares/<shared_id:int>/info      공유 데이터의 정보 갖고오기
    """
    @staticmethod
    @data_shared_download_router.get(
        path='/download',
        status_code=status.HTTP_200_OK)
    def download_shared_data(
        request: Request, 
        shared_id: int, 
        background_tasks: BackgroundTasks
    ):
        try:
            download_root, is_dir = \
                DataSharedManager().download_shared_data(shared_id)
        except DataIsNotShared:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='공유가 되어 있지 않거나 만료되었습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        else:
            data = FileResponse(download_root)
            if is_dir:
                # 디렉토리일 경우 임시파일을 지운다.
                background_tasks.add_task(background_remove_file, download_root)
            return data

    @staticmethod
    @data_shared_download_router.get(
        path='/info',
        status_code=status.HTTP_200_OK)
    def get_info_of_shared(request: Request, shared_id: int):
        
        try:
            data_info = DataSharedManager().get_info_of_shared_data(shared_id)
        except DataIsNotShared:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='공유가 되어 있지 않거나 만료되었습니다.')
        except DataNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='해당 파일 및 디렉토리가 존재하지 않습니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='server error')
        else:
            return data_info