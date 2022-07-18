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
        """
        Token 생성

        :param input_data: 토큰 생성을 위한 데이터
        :return: 토큰
        """
        copied = input_data.copy()
        copied[self.issue_key] = self.issue_name
        copied['iat'] = datetime.datetime.now()
        copied['exp'] = \
            copied['iat'] \
                + datetime.timedelta(seconds=self.token_length * 60)
        return self.token_builder().write(**copied)

    def decode(self, s: str):
        """
        Token 디코딩

        :param s: 디코딩 대상 토큰
        :return:
            {
                'exp': 만료 시각,
                ...
            }
        """
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
