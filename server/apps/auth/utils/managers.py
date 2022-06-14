from architecture.manager.backend_manager import AuthManager
from architecture.manager.base_manager import FrontendManager
from core.token_generators import LoginTokenGenerator


class LoginAuthManager(AuthManager):
    token_generator = LoginTokenGenerator


class AppAuthManager(FrontendManager):

    @staticmethod
    def login(user: str, paswd: str):
        pass