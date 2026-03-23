import uuid

def create_archive(data):

    print('\n\nGot request to "create_archive" with data:\n')
    print(data)

    response = {
        "id": str(uuid.uuid4()),
        "status": "NEW"
    }
    
    return response
