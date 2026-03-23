# НОВЫЕ: Функции для обработки mixed content

def handle_mixed_content(data):
    """Обрабатывает запрос с JSON и файлами"""
    
    if not isinstance(data, dict) or 'fields' not in data or 'files' not in data:
        return {
            'error': 'Invalid multipart data',
            'expected': 'multipart/form-data with fields and files'
        }, 400
    
    response = {
        'message': 'Successfully received mixed content',
        'fields': data['fields'],
        'files_info': {}
    }
    
    # Обрабатываем каждый файл
    for field_name, file_info in data['files'].items():
        response['files_info'][field_name] = {
            'filename': file_info['filename'],
            'size': len(file_info['content']),
            'type': file_info['type'],
            'preview_base64': base64.b64encode(file_info['content'][:100]).decode('ascii') + '...' if len(file_info['content']) > 100 else base64.b64encode(file_info['content']).decode('ascii')
        }
    
    return response

def handle_post_with_image(data):
    """Создает пост с изображением"""
    
    if not isinstance(data, dict):
        return {'error': 'Invalid data'}, 400
    
    response = {
        'post_id': 123,
        'created_at': '2024-01-01T12:00:00Z',
        'post_data': {}
    }
    
    # Обрабатываем текстовые поля
    if 'fields' in data:
        response['post_data'] = data['fields']
    
    # Обрабатываем изображение
    if 'files' in data and 'image' in data['files']:
        image = data['files']['image']
        response['image'] = {
            'filename': image['filename'],
            'size': len(image['content']),
            'type': image['type'],
            'url': f"/api/files/{image['filename']}"
        }
    
    return response

def handle_multi_file_upload(data):
    """Загрузка нескольких файлов с метаданными"""
    
    if not isinstance(data, dict) or 'files' not in data:
        return {'error': 'No files uploaded'}, 400
    
    response = {
        'upload_id': os.urandom(4).hex(),
        'total_files': len(data['files']),
        'files': [],
        'metadata': data.get('fields', {})
    }
    
    for field_name, file_info in data['files'].items():
        file_data = {
            'field': field_name,
            'filename': file_info['filename'],
            'size': len(file_info['content']),
            'type': file_info['type'],
            'hash': base64.b64encode(file_info['content'][:10]).decode('ascii')
        }
        response['files'].append(file_data)
    
    return response

def handle_json_with_base64(data):
    """Принимает JSON с base64 вложенными файлами"""
    
    if not isinstance(data, dict):
        return {'error': 'Invalid JSON'}, 400
    
    response = {
        'received': data,
        'decoded_files': {}
    }
    
    # Ищем поля с base64 данными
    for key, value in data.items():
        if isinstance(value, str) and value.startswith(('data:', 'base64:')):
            try:
                # Пробуем декодировать base64
                if value.startswith('data:'):
                    # Формат data:image/png;base64,...
                    header, encoded = value.split(',', 1)
                    content_type = header.split(';')[0].replace('data:', '')
                else:
                    # Просто base64:...
                    encoded = value.replace('base64:', '')
                    content_type = 'application/octet-stream'
                
                decoded = base64.b64decode(encoded)
                response['decoded_files'][key] = {
                    'decoded_size': len(decoded),
                    'content_type': content_type,
                    'preview': decoded[:50].hex() if len(decoded) > 50 else decoded.hex()
                }
            except:
                response['decoded_files'][key] = 'Failed to decode'
    
    return response

def handle_avatar_update(data):
    """Обновление аватара пользователя"""
    
    if not isinstance(data, dict):
        return {'error': 'Invalid data'}, 400
    
    response = {
        'user_id': data.get('fields', {}).get('user_id', 'unknown'),
        'avatar_updated': False,
        'message': ''
    }
    
    if 'files' in data and 'avatar' in data['files']:
        avatar = data['files']['avatar']
        
        # Проверяем тип файла
        if avatar['type'].startswith('image/'):
            response['avatar_updated'] = True
            response['message'] = 'Avatar updated successfully'
            response['avatar_info'] = {
                'filename': avatar['filename'],
                'size': len(avatar['content']),
                'format': avatar['type']
            }
        else:
            response['message'] = 'File must be an image'
    else:
        response['message'] = 'No avatar file provided'
    
    return response

# Вспомогательные функции для работы с бинарными данными (без изменений)
def handle_binary_file(filename, file_type):
    """Создает mock-бинарный файл заданного типа"""
    
    signatures = {
        'document': b'DOCX FILE SIGNATURE\x00\x00\x00',
        'image': b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00',
        'pdf': b'%PDF-1.4\n%\xE2\xE3\xCF\xD3\n',
        'archive': b'PK\x03\x04',
        'exe': b'MZ\x90\x00',
    }
    
    content = signatures.get(file_type, b'MOCK FILE DATA\x00')
    content += os.urandom(100)
    content += b'\nEND OF MOCK FILE'
    
    mime_types = {
        'document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image': 'image/jpeg',
        'pdf': 'application/pdf',
        'archive': 'application/zip',
        'exe': 'application/x-msdownload',
    }
    
    content_type = mime_types.get(file_type, 'application/octet-stream')
    
    return (content, content_type, filename)

def generate_random_binary(size_bytes):
    """Генерирует случайные бинарные данные заданного размера"""
    return (os.urandom(size_bytes), 'application/octet-stream', f'random_{size_bytes}bytes.bin')

def generate_qr_mock():
    """Генерирует имитацию QR-кода"""
    png_header = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x20,
        0x00, 0x00, 0x00, 0x20,
        0x08, 0x02, 0x00, 0x00, 0x00,
    ])
    
    qr_pattern = bytearray()
    for i in range(32):
        row = bytearray([0xFF if (j + i) % 3 == 0 else 0x00 for j in range(32)])
        qr_pattern.extend(row)
    
    png_footer = bytes([0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82])
    
    mock_png = png_header + bytes(qr_pattern) + png_footer
    
    return (mock_png, 'image/png', 'mock_qr.png')

def generate_dynamic_image(params):
    """Генерирует изображение на основе параметров запроса"""
    
    width = int(params.get('width', ['100'])[0])
    height = int(params.get('height', ['100'])[0])
    color = params.get('color', ['red'])[0]
    
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="{color}"/>
    <circle cx="{width//2}" cy="{height//2}" r="{min(width, height)//4}" fill="white"/>
    <text x="{width//2}" y="{height//2}" font-family="Arial" font-size="12" fill="black" text-anchor="middle">
        Mock Image
    </text>
</svg>'''
    
    return (svg_content.encode('utf-8'), 'image/svg+xml', f'image_{width}x{height}.svg')

def handle_file_upload(data):
    """Обрабатывает загрузку файла"""
    if isinstance(data, bytes):
        file_size = len(data)
        file_preview = base64.b64encode(data[:100]).decode('ascii') if file_size > 100 else base64.b64encode(data).decode('ascii')
        
        return {
            'status': 'success',
            'message': 'File uploaded successfully',
            'file_size': file_size,
            'file_preview_base64': file_preview + ('...' if file_size > 100 else ''),
            'content_type': 'binary/octet-stream'
        }
    else:
        return {
            'status': 'error',
            'message': 'No binary data received'
        }, 400