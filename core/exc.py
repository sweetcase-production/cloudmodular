class UserStorageAlreadyExists(Exception):
    def __init__(self):
        super().__init__("User Storage Already Exists")

class UserNotFound(Exception):
    def __init__(self):
        super().__init__("User Not Found")

class UserAlreadyExists(Exception):
    def __init__(self):
        super().__init__("User Already Exists")

class DataAlreadyExists(Exception):
    def __init__(self):
        super().__init__("Data Already Exists")

class DataNotFound(Exception):
    def __init__(self):
        super().__init__("Data Not Found")

class DataFavoriteNotSelected(Exception):
    def __init__(self):
        super().__init__("This data is not selected by favorite")

class DataIsAlreadyFavorited(Exception):
    def __init__(self):
        super().__init__("This data is already selected by favorite")