import uuid
import random
import string
from datetime import datetime, timedelta

def get_file(id):
    attachments_count = random.randint(0, 15)

    response = {
        "success": True,
        "payLoad": {
            "id": str(uuid.uuid4()),
            "fileName": generate_random_name(),
            "externalId": str(random.randint(10, 10000)),
            "sourceSystem": "1C-Connect",
            "description": random.choice(["Подпись", "Страница", "Паспорт", "СНИЛС", None]),
            "sha512": random_sha(),
            "mimeType": "application/octet-stream",
            "contentSize": random.randint(100, 10000),
            "chronicleId": str(uuid.uuid4()),
            "version": random.randint(1, 10),
            "createdDate": generate_random_datetime(2008, 2025),
            "createdBy": "tst_1cconnect",
            "lastModifiedDate": generate_random_datetime(2008, 2025),
            "lastModifiedBy": None,
            "attachments": [],
            "tags": ["FinRep_1C-Con_SED"]
        }
    }
    
    for _ in range(attachments_count):
        response['payLoad']['attachments'].append({
            "id": str(uuid.uuid4()),
            "name": generate_random_name(),
            "type": random.choice(["SIGN", "PAGE", "PASSPORT", "SNILS"]),
            "description": random.choice(["Подпись", "Страница", "Паспорт", "СНИЛС", None]),
            "createdBy": "tst_1cconnect",
            "createdDate": generate_random_datetime(2008, 2025),
            "lastModifiedDate": generate_random_datetime(2008, 2025),
            "sha512": random_sha(),
            "mimeType": "application/octet-stream",
            "contentSize": random.randint(100, 10000),
            "signCheckResults": [
                {
                    "signResultDate": generate_random_datetime(2008, 2025),
                    "signResult": True,
                    "signResultSystem": "SED",
                    "signCommonName": "CN=\"ООО \"\"Конфетпром\"\"\", O=\"ООО \"G=Геннадий Сергеевич, T=Генеральный директор, SNILS=11223344595, OID.1.2.643.12 STREET=\"3-я Павлоградская ул, д. 13, стр. 2\", INN=779955555519",
                    "signatureDocumentHash": "",
                    "signerCertificateFrom": generate_random_datetime(2008, 2025),
                    "signerCertificateTo": generate_random_datetime(2008, 2025),
                    "signatureDate": generate_random_datetime(2008, 2025),
                    "signerCertificateIssuerName": "CN=\"Тестовый УЦ АО \"\"КАЛУГА АСТРA\"\"\" Теренинский д.6, L=г. Калуга, S=40 Калужская, C=RU, INN=004029017981, OGRN=10",
                    "signerCertificateSerialNumber": random_sha()
                }
            ]
        })
    
    return response

def generate_random_datetime(start_year, end_year):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%dT%H:%M:%S.000+00:00")

def generate_random_name():
    fish_words = [
        "BANK",
        "REPLIST",
        "OGRN",
        "PSB",
        "T-Bank",
        "Alpha",
        "OCTET",
        "DEFINITIVE",
        "SBER",
        "OOO",
        "OAO"
    ]

    return f'{random.choice(fish_words)}_{random.choice(fish_words)}_{str(random.randint(1000, 9999))}_{str(random.randint(1000, 9999))}.xlsx'

def random_sha():
    characters = string.ascii_letters + string.digits
    return ''.join(random.sample(characters, k=len(characters)))
