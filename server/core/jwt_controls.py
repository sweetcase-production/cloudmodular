from architecture.system.jwt import JwtBuilder
from settings.base import JWT

class AppTokenBuilder(JwtBuilder):
    data_map = ('iss', 'email', 'iat', 'exp')
    jwt_key = JWT['key']
    jwt_algorithm = JWT['algorithm']