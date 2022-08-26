import sys
from fastapi import FastAPI

from apps.routers import API_ROUTERS
from middlewares.file_filter import LimitUploadSize
from settings.base import SERVER
def init_app():
    """
    앱 실행기
    """
    # Swagger 지움
    app = FastAPI(redoc_url=None, docs_url=None)
    for router in API_ROUTERS:
        app.include_router(router)
    
    # 파일 업로드 미들웨어 설정
    max_file_size = 1 if 'pytest' in sys.modules \
        else SERVER['maximum-upload-size']
    app.add_middleware(
        LimitUploadSize,
        max_size=max_file_size)
    return app