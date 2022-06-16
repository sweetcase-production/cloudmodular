from abc import ABCMeta
from typing import Any, Dict, Type
import datetime
import time

from jwt import ExpiredSignatureError

from architecture.system.jwt import JwtBuilder


class AuthTokenGenerator(metaclass=ABCMeta):
    token_builder: Type[JwtBuilder] # required key = (issue_key, 'exp', 'iat')
    issue_key: str = 'iss'          # issue key (iss defualt)
    issue_name: str                 # name of issue
    token_length: int               # 분단위

    def generate(self, input_data: Dict[str, Any]):
        copied = input_data.copy()
        copied[self.issue_key] = self.issue_name
        copied['iat'] = datetime.datetime.now()
        copied['exp'] = \
            copied['iat'] \
                + datetime.timedelta(seconds=self.token_length * 60)
        return self.token_builder().write(**copied)

    def decode(self, s: str):
        decoded = self.token_builder().read(s)
        try:
            issue = decoded[self.issue_key]
            expired = decoded['exp']
        except KeyError as e:
            raise e
        if time.time() > expired:
            # 시간 만료됨
            raise ExpiredSignatureError()
        assert issue == self.issue_name
        return decoded
