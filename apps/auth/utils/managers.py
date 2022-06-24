from apps.user.models import User
from apps.user.utils.managers import UserCRUDManager
from architecture.manager.backend_manager import AuthManager
from architecture.manager.base_manager import FrontendManager
from core.token_generators import LoginTokenGenerator


class LoginAuthManager(AuthManager):
    token_generator = LoginTokenGenerator


class AppAuthManager(FrontendManager):

    def login(self, email: str, passwd: str) -> str:
        """
        아이디 패스워드 검증 및 로그인 토큰 발행
        """
        user: User = UserCRUDManager().read(user_email=email)
        if not user or passwd != user.passwd:
            # 유저가 없거나 패스워드가 틀림
            raise ValueError('엽력한 정보가 맞지 않습니다.')
        # 발급
        return LoginAuthManager().generate_token(req={'email': email})
