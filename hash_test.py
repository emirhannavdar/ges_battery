import hashlib
import base64
import uuid

password = 'deneme123'
salt = b'emirhannavdar'

t_sha = hashlib.sha512()
t_sha.update(password.encode('utf-8') + salt)
hashed_password = base64.urlsafe_b64encode(t_sha.digest()).decode('utf-8')

print(hashed_password)