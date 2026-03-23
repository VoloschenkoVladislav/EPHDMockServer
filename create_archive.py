import uuid

def create_archive(data):
    response = {
        "id": str(uuid.uuid4()),
        "status": "NEW"
    }
    
    return response
