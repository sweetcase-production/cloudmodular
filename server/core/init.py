

from fastapi import FastAPI

from apps.routers import API_ROUTERS
def init_app():
    """
    앱 실행기
    """
    app = FastAPI()
    for router in API_ROUTERS:
        app.include_router(router)
    return app