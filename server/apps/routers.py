from apps.auth.views import auth_router
from apps.user.views import user_router, user_search_router

API_ROUTERS = [
    auth_router,
    user_search_router,
    user_router,
]