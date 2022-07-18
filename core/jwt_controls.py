from architecture.system.jwt import JwtBuilder
from settings.base import JWT


class AppTokenBuilder(JwtBuilder):
    """
    Token 생성 또는 읽을 때 사용
    """
    data_map = ('iss', 'email', 'iat', 'exp')
    jwt_key = JWT['key']
    jwt_algorithm = JWT['algorithm']
