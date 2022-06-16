import os
import shutil


from architecture.query.crud import QueryCRUD, QueryCreator, QueryDestroyer
from core.exc import UserStorageAlreadyExists
from settings.base import SERVER


class UserStorageCreator(QueryCreator):
    def __call__(self, user_id: int, force: bool = False) -> str:
        """
        해당 유저가 사용할 디렉토리들을 생성한다.
        DB상에서의 User를 처리한 다음 사용하는 것을 권장한다.

        :params user_id: 대상 유저 아이디
        :params force: 유저의 디렉토리가 이미 존재할 경우 True를 하면 강제로 다시 생성한다.

        :return: 실제 주소

        :exception UserStorageAlreadyExists: 이미 해당 User Storage가 존재함
        """
        # root 지정
        main_root = f'{SERVER["storage"]}/storage/{user_id}'
        if os.path.isdir(main_root):
            # 이미 존재하는 경우
            if force:
                # 강제성이 있는 경우 죄다 삭제
                shutil.rmtree(main_root)
            else:
                # 아니면 Error 호출
                raise UserStorageAlreadyExists()
        # 새로 구축
        os.mkdir(main_root)
        return main_root

class UserStorageDestroyer(QueryDestroyer):
    def __call__(self, user_id: int):

        main_root = f'{SERVER["storage"]}/storage/{user_id}'
        shutil.rmtree(main_root)


class UserStorageQuery(QueryCRUD):
    creator = UserStorageCreator
    destroyer = UserStorageDestroyer