import uuid
import random
from datetime import datetime, timedelta

def get_documents(data):

    print('\n\nGot request to "get_documents" with data:\n')
    print(data)

    if 'clientId' not in data:
        return {
            "status": "ERROR",
            "errors": ["missing 'clientId' field"],
            "message": "clientId field is required"
        }, 400
    if 'productId' not in data:
        return {
            "status": "ERROR",
            "errors": ["missing 'clientId' field"],
            "message": "clientId field is required"
        }, 400
    if 'types' not in data:
        return {
            "status": "ERROR",
            "errors": ["missing 'types' field"],
            "message": "types field is required"
        }, 400

    document_count = random.randint(0, 15)

    response = {
        "success": True,
        "payLoad": {
            "total": document_count,
            "data": []
        }
    }

    for _ in range(document_count):
        response['payLoad']['data'].append({
            "id": str(uuid.uuid4()),
            "type": random.choice(data['types']) if data['types'] else str(random.randint(1000, 9999)),
            "name": "Паспорт",
            "number": str(random.randint(100000, 999999)),
            "date": None,
            "status": "ACTIVE",
            "comment": None,
            "productIds": [str(uuid.uuid4())],
            "attachmentIds": [str(uuid.uuid4())],
            "createdDate": generate_random_datetime(2008, 2025),
            "lastModifiedDate": generate_random_datetime(2008, 2025)
        })
    
    return response

def generate_random_datetime(start_year, end_year):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%dT%H:%M:%S")
