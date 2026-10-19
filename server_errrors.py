import random

ERROR_CHANCE = 0

def error_chance(func):
    def wrapper(*args, **kwargs):
        if random.randint(0, 100) < ERROR_CHANCE:
            return {
                "status": "ERROR",
                "errors": ["not found"],
                "message": "Not found"
            }, 404
        else:
            return func(*args, **kwargs)
    return wrapper
