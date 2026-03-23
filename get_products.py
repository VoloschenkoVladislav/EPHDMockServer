import uuid
import random
from datetime import datetime, timedelta

def get_products(clientId):

    print('\n\nGot request to "get_products" with clientId:\n')
    print(clientId)

    numberOfProducts = random.randint(0, 10)

    types = [
        "LIMIT_OPEN",
        "OVERDRAFT",
        "LIMIT_CLOSED",
        "DEFAULT_TYPE",
        "SIMPLE_TYPE"
    ]

    names = [
        "433 Овердрафт",
        "651 Лимит открыт",
        "317 Лимит открыт",
        "344 Лимит открыт",
        "612 Овердрафт",
        "84 Овердрафт"
    ]

    response = {
        "success": True,
        "payLoad": {
            "total": numberOfProducts,
            "data": []
        }
    }

    for _ in range(numberOfProducts):
        response['payLoad']['data'].append({
            "id": str(uuid.uuid4()),
            "name": random.choice(names),
            "type": random.choice(types),
            "contractNumber": str(random.randint(100000000000, 999999999999)),
            "contractDate": generate_random_date(),
            "accountNumber": str(random.randint(100000000000, 999999999999)),
            "status": "ACTIVE",
            "sapId": str(random.randint(100000000000, 999999999999))
        })
    
    return response


def generate_random_date(start_year=2010, end_year=2026):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    random_date = start_date + timedelta(days=random_days)

    return random_date.strftime("%Y-%m-%d")
