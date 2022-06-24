from abc import ABCMeta
from collections.abc import Sequence
from typing import Any, Dict
import jwt
import time
import datetime


class JwtBuilder(metaclass=ABCMeta):
    data_map: Sequence[str]
    jwt_key: str
    jwt_algorithm: str

    def _save_data(self, k: str, v: Any, m: Dict[str, Any]):
        """
        iat: 발행 시각
        exp: 만료 시각

        이 경우, 따로 처리를 한다.
        """
        if k == 'iat':
            # iat의 데이터타입은 datetime.datetime이어야 한다.
            if not isinstance(v, datetime.datetime):
                raise ValueError('iat writing failed')
            m[k] = time.mktime(v.timetuple())
        elif k == 'exp':
            # exp 데이터 타입은 datetime이어야 한다.
            if not isinstance(v, datetime.datetime):
                raise ValueError('exp writing failed')
            m[k] = time.mktime(v.timetuple())
        else:
            m[k] = v
    
    def write(self, **kwargs) -> str:
        input_data: Dict[str, Any] = dict()

        for k, v in kwargs.items():
            if k not in self.data_map:
                continue
            self._save_data(k=k, v=v, m=input_data)
        # Load
        return jwt.encode(input_data, self.jwt_key, self.jwt_algorithm)
            

    def read(self, token: str):
        decoded = jwt.decode(token, self.jwt_key, algorithms=[self.jwt_algorithm])
        return decoded