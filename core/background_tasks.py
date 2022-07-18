import os


def background_remove_file(path: str):
    """
    백그라운드 상에서의 파일 삭제
    주로 임시파일을 클라이언트에 보낸 다음 파일을 삭제 할 때 사용된다.
    
    :params path: 삭제 대상 파일 루트
    """
    os.remove(path)