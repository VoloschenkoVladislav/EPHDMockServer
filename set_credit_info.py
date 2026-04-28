import uuid
from server_errrors import error_chance

@error_chance
def set_credit_info(data):
    response = {
        "success": True,
        "payLoad": {
            "requestId": str(uuid.uuid4()),
            "status": "Completed",
            "errorsCount": 0,
            "errors": [],
            "clientResults": [],
            "packageResults": [],
            "documentResults": [],
            "holdingResults": []
        }
    }

    if 'clients' in data:
        for client in data['clients']:
            response['payLoad']['clientResults'].append({
                "localId": client['localId'],
                "status": "OK",
                "message": "Клиент успешно изменен",
                "errors": [],
                "objectId": str(uuid.uuid4())
            })
    if 'packages' in data:
        for package in data['packages']:
            response['payLoad']['packageResults'].append({
                "localId": package['localId'],
                "status": "OK",
                "message": "Продукт успешно изменен",
                "errors": [],
                "objectId": str(uuid.uuid4())
            })
    if 'documents' in data:
        for document in data['documents']:
            response['payLoad']['documentResults'].append({
                "localId": document['localId'],
                "status": "OK",
                "message": "Документ успешно изменен",
                "errors": [],
                "objectId": str(uuid.uuid4())
            })
    if 'holdings' in data:
        for holding in data['holdings']:
            response['payLoad']['holdingResults'].append({
                "localId": holding['localId'],
                "status": "OK",
                "message": "Холдинг успешно изменен",
                "errors": [],
                "objectId": str(uuid.uuid4())
            })
    
    return response
