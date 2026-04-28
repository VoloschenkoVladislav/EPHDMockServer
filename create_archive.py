import uuid
from server_errrors import error_chance

@error_chance
def create_archive(data):
    response = {
        "id": str(uuid.uuid4()),
        "status": "NEW"
    }
    
    return response
