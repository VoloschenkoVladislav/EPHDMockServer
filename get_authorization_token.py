import random
import string
from server_errrors import error_chance

def get_authorization_token():
    response = {
        "access_token": random_sha(),
        "refresh_token": random_sha(),
        "expires_in": 300,
        "refresh_expires_in": 300,
    }
    return response

def random_sha():
    characters = string.ascii_letters + string.digits
    return ''.join(random.sample(characters, k=len(characters)))
