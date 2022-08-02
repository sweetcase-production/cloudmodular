

from fastapi import FastAPI

from apps.routers import API_ROUTERS
def init_app():
    """
    앱 실행기
    """
    # Swagger 지움
    app = FastAPI(redoc_url=None, docs_url=None)
    for router in API_ROUTERS:
        app.include_router(router)
    return app