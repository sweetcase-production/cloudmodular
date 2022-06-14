

from fastapi import APIRouter, Request, status


auth_router = APIRouter(
    prefix='/api/auth',
    tags=['auth'],
    responses={404: {'error': 'Not Found'}}
)

class TokenGenerateView:
    """
    (POST)  /api/auth/token     토큰 발행
    """
    @staticmethod
    @auth_router.post(
        path='/token',
        status_code=status.HTTP_201_CREATED,
    )
    async def get_token(request: Request):
        pass
