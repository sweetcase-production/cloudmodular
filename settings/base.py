import os

from dotenv import load_dotenv
load_dotenv()

def _get_database_info():
    t = os.getenv('DB_TYPE')
    if t == 'sqlite':
        return dict()
    else:
        return {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT')),
            'database': os.getenv('DB_DATABASE'),
            'user': os.getenv('DB_USER'),
            'passwd': os.getenv('DB_PASSWD'),
        }

SERVER = {
    'host': os.getenv('SERVER_HOST'),
    'port': int(os.getenv('SERVER_PORT')),
    'storage': os.getenv('SERVER_STORAGE') + '/cloudmodular',
    'data-shared-length': int(os.getenv('DATA_SHARED_LENGTH')) * 24 * 60,
    'maximum-upload-size': int(os.getenv('MAX_UPLOAD_LEN')),
}
DATABASE = {
    'type': os.getenv('DB_TYPE'),
    'data': _get_database_info(),
}
ADMIN = {
    'email': os.getenv('ADMIN_EMAIL'),
    'email_2nd_pswd': os.getenv('ADMIN_EMAIL_PASSWD'),
    'passwd': os.getenv('ADMIN_PASSWD'),
}
JWT = {
    'key': os.getenv('JWT_KEY'),
    'algorithm': os.getenv('JWT_ALGORITHM'),
}