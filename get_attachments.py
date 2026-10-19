import os
from server_errrors import error_chance

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@error_chance
def get_attachments(id):
    try:
        file_path = os.path.join(BASE_DIR, 'test_file.pdf')
        with open(file_path, 'rb') as f:
            content = f.read()
        return content
    except Exception as e:
        return {
            'error': f'Error reading file: {str(e)}',
            'status': 500
        }, 500
