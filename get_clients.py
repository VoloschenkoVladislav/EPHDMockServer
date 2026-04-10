import uuid
import random
from datetime import datetime, timedelta

def get_clients(params):
    full_name = params.get('fullName', [None])[0]
    passport_series = params.get('passportSeries', [None])[0]
    passport_number = params.get('passportNumber', [None])[0]
    id = params.get('id', [None])[0]
    limit = int(params.get('limit', [10])[0])
    offset = int(params.get('offset', [0])[0])
    sort = params.get('sort', ['fullName'])[0]
    direct = params.get('direct', ['asc'])[0]

    client_count = random.randint(0, 1)

    all_clients = generate_clients(id, full_name, passport_series, passport_number, count=client_count)
    sorted_clients = sort_clients(all_clients, sort, direct)
    paginated_clients = sorted_clients[offset:offset + limit]

    response = {
        "success": True,
        "payLoad": {
            "count": len(paginated_clients),
            "clients": paginated_clients
        }
    }
    
    return response

def generate_clients(id, full_name, passport_series, passport_number, count=5):
    clients = []
    
    for i in range(count):
        clients.append({
            "id": id,
            "fullName": full_name if full_name else generate_random_name(),
            "passportSeries": passport_series if passport_series else str(random.randint(1000, 9999)),
            "passportNumber": passport_number if passport_number else str(random.randint(100000, 999999)),
            "birthDate": generate_random_date(1960, 2008),
            "snils": str(random.randint(10000000000, 99999999999))
        })
    
    return clients

def sort_clients(clients, sort_field, direction):
    sortable_fields = ['id', 'passportSeries', 'fullName', 'passportNumber', 'birthDate', 'snils']
    
    if sort_field not in sortable_fields:
        sort_field = 'id'
    
    sorted_clients = clients.copy()
    
    reverse = direction.lower() == 'desc'
    sorted_clients.sort(key=lambda x: x.get(sort_field, ''), reverse=reverse)
    
    return sorted_clients

def generate_random_date(start_year, end_year):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%d")

def generate_random_name():
    last_names = ["Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов", "Васильев", "Михайлов", "Федоров", "Морозов"]
    first_names = ["Иван", "Петр", "Сергей", "Андрей", "Алексей", "Дмитрий", "Михаил", "Александр", "Владимир", "Николай"]
    patronymics = ["Иванович", "Петрович", "Сергеевич", "Андреевич", "Алексеевич", "Дмитриевич", "Михайлович", "Александрович", "Владимирович", "Николаевич"]
    
    return f"{random.choice(last_names)} {random.choice(first_names)} {random.choice(patronymics)}"
