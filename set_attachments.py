import uuid
import hashlib
import random
from datetime import datetime

def set_attachments(data):
    fields = {}
    files = {}
    
    if isinstance(data, dict) or True:
        if 'fields' in data and 'files' in data:
            fields = data['fields']
            files = data['files']
        else:
            for key, value in data.items():
                if isinstance(value, dict) and 'content' in value and 'filename' in value:
                    files[key] = value
                else:
                    fields[key] = value
    
    if 'meta' not in fields:
        return {
            "status": "ERROR",
            "errors": ["missing 'meta' field"],
            "message": "meta field is required"
        }, 400
    
    if 'file' not in files:
        return {
            "status": "ERROR",
            "errors": ["missing 'file' in files"],
            "message": "file is required"
        }, 400
    
    main_file = files['file']
    
    meta_data = fields['meta']
    if isinstance(meta_data, str):
        try:
            import json
            meta_data = json.loads(meta_data)
        except:
            pass
    
    response = {
        "status": "SUCCESS",
        "errors": [],
        "message": "Файлы успешно загружены в хранилище",
        "fileResult": {
            "akdId": str(uuid.uuid4()),
            "externalId": str(random.randint(1, 10000)),
            "sha512": hashlib.sha256(main_file['content']).hexdigest(),
            "externalCreatedDate": datetime.now().isoformat()
        },
        "attachmentResult": []
    }
    
    for field_name, file_info in files.items():
        if field_name != 'file':
            response['attachmentResult'].append({
                'akdId': str(uuid.uuid4()),
                'sha512': hashlib.sha256(file_info['content']).hexdigest()
            })
    
    return response
