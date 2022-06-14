from abc import ABC, ABCMeta


class BaseManager(metaclass=ABCMeta):
    """
    모든 Manager의 최상위
    """
    pass

class FrontendManager(BaseManager, ABC):
    """
    요청 들어올 때 바로 반응하는 Manager로
    오버라이딩이 허용됨
    """
    pass

class BackendManager(BaseManager, ABC):
    """
    Frontend Manager의 역할을 보조하는 매니저
    오버라이딩이 권장되지 않음
    """
    pass