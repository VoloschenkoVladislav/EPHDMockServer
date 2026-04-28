#!/usr/bin/env python3
import json
import re
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Импорт ваших обработчиков
from set_attachments import set_attachments
from set_credit_info import set_credit_info
from get_attachments import get_attachments
from get_products import get_products
from get_clients import get_clients
from get_documents import get_documents
from create_archive import create_archive
from get_archive import get_archive
from get_file import get_file


class MultipartParser:
    """Класс для парсинга multipart/form-data без использования cgi"""
    
    @staticmethod
    def parse(headers, body):
        """
        Парсит multipart/form-data данные
        
        Args:
            headers: HTTP headers (dict-like)
            body: тело запроса (bytes)
        
        Returns:
            dict: {'fields': {...}, 'files': {...}}
        """
        content_type = headers.get('Content-Type', '')
        
        # Извлекаем boundary
        boundary_match = re.search(r'boundary=([^;\s]+)', content_type)
        if not boundary_match:
            return {'fields': {}, 'files': {}}
        
        boundary = boundary_match.group(1).encode()
        
        # Разделяем на части
        parts = body.split(b'--' + boundary)
        
        result = {
            'fields': {},
            'files': {}
        }
        
        for part in parts:
            if not part or part == b'--\r\n' or part == b'--':
                continue
            
            # Убираем \r\n в начале
            if part.startswith(b'\r\n'):
                part = part[2:]
            
            # Разделяем заголовки и содержимое
            headers_end = part.find(b'\r\n\r\n')
            if headers_end == -1:
                continue
            
            headers_section = part[:headers_end].decode('utf-8', errors='replace')
            content = part[headers_end + 4:]
            
            # Убираем завершающий \r\n если есть
            if content.endswith(b'\r\n'):
                content = content[:-2]
            
            # Парсим заголовки
            headers_dict = {}
            for line in headers_section.split('\r\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers_dict[key.strip()] = value.strip()
            
            # Извлекаем имя поля
            content_disposition = headers_dict.get('Content-Disposition', '')
            name_match = re.search(r'name="([^"]+)"', content_disposition)
            if not name_match:
                continue
            
            field_name = name_match.group(1)
            
            # Проверяем, является ли это файлом
            filename_match = re.search(r'filename="([^"]+)"', content_disposition)
            
            if filename_match:
                # Это файл
                filename = filename_match.group(1)
                content_type = headers_dict.get('Content-Type', 'application/octet-stream')
                
                result['files'][field_name] = {
                    'filename': filename,
                    'content': content,
                    'type': content_type
                }
            else:
                # Это текстовое поле
                try:
                    result['fields'][field_name] = content.decode('utf-8')
                except UnicodeDecodeError:
                    result['fields'][field_name] = content.decode('latin-1')
        
        return result


class ChunkedReader:
    """Класс для чтения chunked encoded данных"""
    
    @staticmethod
    def read_chunked(rfile):
        """
        Читает данные в формате chunked transfer encoding
        
        Args:
            rfile: файловый объект для чтения
        
        Returns:
            bytes: собранные данные
        """
        data = bytearray()
        
        while True:
            # Читаем размер чанка (в hex)
            line = ChunkedReader._read_line(rfile)
            if not line:
                break
            
            # Парсим размер чанка
            try:
                chunk_size = int(line.strip().split(b';')[0], 16)
            except ValueError:
                break
            
            if chunk_size == 0:
                # Конец данных
                # Пропускаем завершающие \r\n
                ChunkedReader._read_line(rfile)
                break
            
            # Читаем чанк
            chunk = rfile.read(chunk_size)
            if len(chunk) != chunk_size:
                break
            
            data.extend(chunk)
            
            # Пропускаем \r\n после чанка
            ChunkedReader._read_line(rfile)
        
        return bytes(data)
    
    @staticmethod
    def _read_line(rfile):
        """Читает строку из rfile до \r\n"""
        line = bytearray()
        while True:
            b = rfile.read(1)
            if not b:
                break
            line.append(b[0])
            if len(line) >= 2 and line[-2:] == b'\r\n':
                return bytes(line[:-2])
        return bytes(line)


class MockHandler(BaseHTTPRequestHandler):
    # Разрешаем все хосты для production (None) или указываем конкретные
    ALLOWED_HOSTS = None  # None = разрешить все хосты
    
    endpoints = {
        'GET': {
            r'^/psbfs/api/v1\.1/files/([^/]+)/binaries$': lambda self, match, _: get_attachments(match.group(1)),
            r'^/api/integration/products/([^/]+)$': lambda self, match, _: get_products(match.group(1)),
            r'^/api/v1/ul/clients$': lambda self, match, params: get_clients(params),
            r'^/psbfs/api/v1.1/jobs/package/([^/]+)/binaries$': lambda self, match, params: get_archive(match.group(1)),
            r'^/api/v1/files/([^/]+)/info$': lambda self, match, params: get_file(match.group(1))
        },
        'POST': {
            '/psbfs/api/v1.1/files/attachments': lambda self, data: set_attachments(data),
            '/psbfs/api/v2/dossier': lambda self, data: set_credit_info(data),
            '/api/integration/documents/search': lambda self, data: get_documents(data),
            '/psbfs/api/v1.1/jobs/package': lambda self, data: create_archive(data)
        },
        'PUT': {},
        'DELETE': {}
    }
    
    def _check_host(self):
        """Проверяет, разрешен ли хост"""
        if self.ALLOWED_HOSTS is None:
            return True  # Разрешаем все хосты
        
        host = self.headers.get('Host', '')
        host = host.split(':')[0]
        
        if host not in self.ALLOWED_HOSTS:
            self._send_response({
                'error': 'Forbidden',
                'message': f'Host {host} is not allowed'
            }, 403)
            return False
        return True
    
    def _set_headers(self, status_code=200, content_type='application/json', extra_headers=None):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Content-Disposition')
        
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        
        self.end_headers()
    
    def _parse_multipart(self):
        """Парсит multipart/form-data запрос с поддержкой chunked encoding"""
        content_type = self.headers.get('Content-Type', '')
        
        if not content_type.startswith('multipart/form-data'):
            return None
        
        try:
            # Определяем способ получения данных
            transfer_encoding = self.headers.get('Transfer-Encoding', '')
            content_length = self.headers.get('Content-Length')
            
            if 'chunked' in transfer_encoding.lower():
                # Читаем chunked данные
                body = ChunkedReader.read_chunked(self.rfile)
            elif content_length:
                # Читаем с известной длиной
                body = self.rfile.read(int(content_length))
            else:
                # Читаем все доступные данные
                body = self.rfile.read()
            
            if not body:
                return {'fields': {}, 'files': {}}
            
            return MultipartParser.parse(self.headers, body)
            
        except Exception as e:
            print(f"Error parsing multipart: {e}")
            return {'fields': {}, 'files': {}}
    
    def _parse_body(self):
        """Парсит тело запроса с поддержкой различных Content-Type и Transfer-Encoding"""
        
        content_length = int(self.headers.get('Content-Length', 0))
        if not content_length:
            return None
        
        content_type = self.headers.get('Content-Type', '')
        transfer_encoding = self.headers.get('Transfer-Encoding', '')
        
        # Получаем тело запроса
        body = None
        
        if 'chunked' in transfer_encoding.lower():
            # Читаем chunked данные
            body = ChunkedReader.read_chunked(self.rfile)
        elif content_length:
            # Читаем с известной длиной
            body = self.rfile.read(content_length)
        else:
            # Нет информации о длине - читаем все доступные данные
            body = self.rfile.read()
        
        if body is None or len(body) == 0:
            return None
        
        # Обработка multipart/form-data
        if content_type.startswith('multipart/form-data'):
            return MultipartParser.parse(self.headers, body)
        
        # Обработка JSON
        elif content_type.startswith('application/json'):
            try:
                return json.loads(body.decode('utf-8'))
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                return body.decode('utf-8')
        
        # Обработка обычных бинарных данных
        else:
            return body
    
    def _send_response(self, data, status=200):
        self._set_headers(status)
        if isinstance(data, (dict, list)):
            response = json.dumps(data, ensure_ascii=False, indent=2)
            self.wfile.write(response.encode('utf-8'))
        elif isinstance(data, bytes):
            self.wfile.write(data)
        else:
            self.wfile.write(str(data).encode('utf-8'))
    
    def _send_binary_response(self, data, content_type, filename=None, status=200):
        headers = {}
        if filename:
            headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        self._set_headers(status, content_type, headers)
        self.wfile.write(data)
    
    def _handle_request(self, method, path):
        """Основной метод обработки запросов"""
        
        # Проверяем хост
        if not self._check_host():
            return
        
        parsed = urlparse(path)
        clean_path = parsed.path
        query_params = parse_qs(parsed.query)
        
        # Сначала ищем точное совпадение
        handler = self.endpoints.get(method, {}).get(clean_path)
        
        if handler:
            try:
                if method in ['POST', 'PUT']:
                    data = self._parse_body()
                    result = handler(self, data)
                else:
                    import inspect
                    if inspect.signature(handler).parameters:
                        result = handler(self, query_params)
                    else:
                        result = handler(self)
                
                self._send_response(result)
                return
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._send_response({'error': str(e)}, 500)
                return
        
        # Если не нашли точное совпадение, ищем по regex паттернам
        for pattern, pattern_handler in self.endpoints.get(method, {}).items():
            if pattern.startswith('^'):  # Это regex паттерн
                match = re.match(pattern, clean_path)
                if match:
                    try:
                        # Для regex паттернов передаем match объект и query_params
                        result = pattern_handler(self, match, query_params)
                        
                        # Обработка различных типов ответов
                        if isinstance(result, tuple) and len(result) >= 2:
                            if len(result) == 2:
                                data, content_type = result
                                self._send_binary_response(data, content_type)
                            else:
                                data, content_type, filename = result
                                self._send_binary_response(data, content_type, filename)
                        else:
                            self._send_response(result)
                        return
                        
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        self._send_response({'error': str(e)}, 500)
                        return
        
        # Если ничего не нашли
        self._send_not_found(clean_path)
    
    def _send_not_found(self, path):
        self._send_response({
            'error': 'Not found',
            'path': path,
            'message': f'Endpoint {path} not implemented'
        }, 404)
    
    # HTTP методы
    def do_GET(self):
        self._handle_request('GET', self.path)
    
    def do_POST(self):
        self._handle_request('POST', self.path)
    
    def do_PUT(self):
        self._handle_request('PUT', self.path)
    
    def do_DELETE(self):
        self._handle_request('DELETE', self.path)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Content-Disposition')
        self.end_headers()
    
    def log_message(self, format, *args):
        # Включаем логирование для production
        print(f"[{self.address_string()}] {format % args}")


def get_local_ip():
    """Получает локальный IP адрес машины"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def run_server(port=8000, host='0.0.0.0'):
    server_address = (host, port)
    httpd = HTTPServer(server_address, MockHandler)
    
    print("=" * 70)
    print("🚀 MOCK SERVER STARTED")
    print("=" * 70)
    print(f"📡 Binding: {host}:{port}")
    print(f"🌐 Server URLs:")
    print(f"   - http://localhost:{port}")
    print(f"   - http://{get_local_ip()}:{port}")
    print()
    print("📋 Available endpoints:")
    print("   GET  /psbfs/api/v1.1/files/{id}/binaries")
    print("   GET  /api/integration/products/{clientId}")
    print("   GET  /api/v1/ul/clients")
    print("   GET  /psbfs/api/v1.1/jobs/package/{jobId}/binaries")
    print("   GET  /api/v1/files/{fileId}/info")
    print("   POST /psbfs/api/v1.1/files/attachments")
    print("   POST /psbfs/api/v2/dossier")
    print("   POST /api/integration/documents/search")
    print("   POST /psbfs/api/v1.1/jobs/package")
    print()
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 70)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        httpd.server_close()


if __name__ == '__main__':
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    host = sys.argv[2] if len(sys.argv) > 2 else '0.0.0.0'
    
    run_server(port, host)