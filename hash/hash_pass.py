import hashlib
import base64


def get_hashed_password(username: str, password: str):
    passwordd = password.encode('utf-8')
    salt = username.encode('utf-8')

    t_sha = hashlib.sha512()
    t_sha.update(passwordd + salt)
    hashed_password = base64.urlsafe_b64encode(t_sha.digest()).decode('utf-8')
    return hashed_password
