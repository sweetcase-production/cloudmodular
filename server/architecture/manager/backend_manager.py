from abc import ABC, abstractmethod
from typing import Dict, Any, Type

from architecture.manager.base_manager import BackendManager
from architecture.query.auth import AuthTokenGenerator
from architecture.query.crud import QueryCRUD


class CRUDManager(BackendManager, ABC):
    """
    쿼리 목적의 백엔드 매니저

    데이터베이스가 아니어도 특정 리소스에 접근 및 관리한다면
    이 매니저를 상속받아서 사용한다.
    """

    @abstractmethod
    def create(self, *args, **kwargs):
        pass

    @abstractmethod
    def update(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def read(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def destroy(self, *args, **kwargs):
        pass

    @abstractmethod
    def search(self, *args, **kwargs):
        pass

class AuthManager(BackendManager):
    
    token_generator: Type[AuthTokenGenerator]

    def generate_token(self, req: Dict[str, Any]):
        return self.token_generator().generate(req)

    def read_token(self, token: str):
        return self.token_generator().decode(token)