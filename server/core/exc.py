class UserStorageAlreadyExists(Exception):
    def __init__(self):
        super().__init__("User Storage Already Exists")

class UserNotFound(Exception):
    def __init__(self):
        super().__init__("User Not Found")

class UserAlreadyExists(Exception):
    def __init__(self):
        super().__init__("User Already Exists")
