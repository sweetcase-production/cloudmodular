from fastapi import HTTPException, Request, status

from apps.auth.utils.managers import AppAuthManager
from apps.routers import auth_router

TOKEN_ISSUES = ('logined', 'passwd-finding', 'first-setting')

class TokenGenerateView:
    """
    (POST)  /api/auth/token     토큰 발행
    """
    @staticmethod
    @auth_router.post(
        path='/token',
        status_code=status.HTTP_201_CREATED)
    async def get_token(request: Request):
        req = await request.json()
        try:
            token_issue = req['issue']
            if token_issue == 'login':
                # 로그인 토큰 요청
                email = req['email']
                passwd = req['passwd']
                token = AppAuthManager().login(email, passwd)
                return {'token': token}
            else:
                # 알 수 없는 요청
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='알 수 없는 요청입니다.')
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='요청 데이터가 부족합니다.')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="server errror")