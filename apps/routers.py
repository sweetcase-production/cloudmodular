from apps.auth.views import auth_router
from apps.user.views import user_router, user_search_router
from apps.storage.views import storage_router
from apps.data_favorite.views import data_favorite_router

API_ROUTERS = [
    auth_router,
    data_favorite_router,
    storage_router,
    user_search_router,
    user_router,
]