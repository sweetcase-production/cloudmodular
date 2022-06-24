from abc import ABC, ABCMeta, abstractmethod

from typing import Type

class QueryMethod(metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class QueryReader(QueryMethod, ABC):
    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class QueryCreator(QueryMethod, ABC):
    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class QueryUpdator(QueryMethod, ABC):
    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class QueryDestroyer(QueryMethod, ABC):
    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class QuerySearcher(QueryMethod, ABC):
    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass

class QueryCRUD(metaclass=ABCMeta):
    creator: Type[QueryCreator] = None
    reader: Type[QueryReader] = None
    updator: Type[QueryUpdator] = None
    destroyer: Type[QueryDestroyer] = None
    searcher: Type[QuerySearcher] = None

    def _run_query(self, method: Type[QueryMethod], *args, **kwargs):
        if not method:
            raise PermissionError('method not allowed')
        return method()(*args, **kwargs)

    def create(self, *args, **kwargs):
        return self._run_query(self.creator, *args, **kwargs)

    def read(self, *args, **kwargs):
        return self._run_query(self.reader, *args, **kwargs)

    def update(self, *args, **kwargs):
        return self._run_query(self.updator, *args, **kwargs)

    def destroy(self, *args, **kwargs):
        return self._run_query(self.destroyer, *args, **kwargs)
    
    def search(self, *args, **kwargs):
        return self._run_query(self.searcher, *args, **kwargs)

