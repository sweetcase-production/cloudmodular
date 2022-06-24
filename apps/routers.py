from apps.auth.views import auth_router
from apps.user.views import user_router, user_search_router
from apps.storage.views import storage_router

API_ROUTERS = [
    auth_router,
    user_search_router,
    user_router,
    storage_router,
]