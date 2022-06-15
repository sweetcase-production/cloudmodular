from fastapi import APIRouter, HTTPException, Request, status

from apps.auth.utils.managers import AppAuthManager

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
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='입력한 정보가 맞지 않습니다.')
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="server errror")