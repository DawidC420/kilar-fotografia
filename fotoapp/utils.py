from cryptography.fernet import Fernet
from django.conf import settings


fernet = Fernet(settings.ENCRYPTION_KEY)

def encrypt_path(path):
    return fernet.encrypt(path.encode()).decode()

def decrypt_path(token):
    return fernet.decrypt(token.encode()).decode()