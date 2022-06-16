from abc import ABC, ABCMeta
from typing import Any, Callable


class PermissionChecker(metaclass=ABCMeta):
    """
    권한 체크
    """
    checked: bool
    func: Callable
    ref_v: Any = None

    def __init__(self, v: Any):
        self.checked = self.func(self.ref_v, v)
    
    def __bool__(self):
        return self.checked

    def __and__(self, o):
        if bool(self) is False:
            o.checked = False
        return o
    
    def __or__(self, o):
        if bool(self):
            o.checked = True
        return o


class PermissionSameUserChecker(PermissionChecker):
    """
    동일한 유저인 지 체크
    """
    ref_v = None
    func = lambda _, o1, o2: o1 == o2

    def __init__(self, v: str, target: str):
        self.ref_v = target
        super().__init__(v)

class PermissionIssueChecker(PermissionChecker, ABC):
    """
    JWT issue에 따른 체크
    """
    func = lambda _, o1, o2: o1 == o2


class PermissionUserLevelChecker(PermissionChecker, ABC):
    """
    유저 타입 체크
    """
    func = lambda _, o1, o2: o1 == o2
