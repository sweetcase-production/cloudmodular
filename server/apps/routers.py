from fastapi import APIRouter


auth_router = APIRouter(
    prefix='/api/auth',
    tags=['auth'],
    responses={404: {'error': 'Not Found'}}
)

API_ROUTERS = [
    auth_router,
]