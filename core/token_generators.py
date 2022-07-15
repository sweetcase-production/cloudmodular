from typing import Tuple, Type

from architecture.query.auth import AuthTokenGenerator
from core.jwt_controls import AppTokenBuilder


class LoginTokenGenerator(AuthTokenGenerator):
    token_builder = AppTokenBuilder
    issue_key = 'iss'
    issue_name = 'logined'
    token_length = 60 * 24 * 30 # 30일

class PasswordFindingTokenGenerator(AuthTokenGenerator):
    token_builder = AppTokenBuilder
    issue_key = 'iss'
    issue_name = 'passwd-finding'
    token_length = 5    # 5분

class FirstSettingTokenGenerator(AuthTokenGenerator):
    token_builder = AppTokenBuilder
    issue_key = 'iss'
    issue_name = 'first-setting'
    token_length = 10

def decode_token(token: str, gen_type: Type[AuthTokenGenerator]):
    try:
        decoded_token = gen_type().decode(token)
        op_email = decoded_token['email']
        issue = decoded_token['iss']
    except Exception:
        raise PermissionError('token decode/checking failed')
    return op_email, issue