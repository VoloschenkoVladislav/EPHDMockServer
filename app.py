import json
import cgi
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from set_attachments import set_attachments
from set_credit_info import set_credit_info
from get_attachments import get_attachments
from get_products import get_products
from get_clients import get_clients
from get_documents import get_documents
from create_archive import create_archive
from get_archive import get_archive

class MockHandler(BaseHTTPRequestHandler):
    endpoints = {
        'GET': {
            r'^/psbfs/api/v1\.1/files/(\d+)/binaries$': lambda self, match, _: get_attachments(match.group(1)),
            r'^/api/integration/products/([^/]+)$': lambda self, match, _: get_products(match.group(1)),
            r'^/api/v1/ul/clients$': lambda self, match, params: get_clients(params),
            r'^/psbfs/api/v1.1/jobs/package/([^/]+)/binaries$': lambda self, match, params: get_archive(params)
        },
        'POST': {
            '/psbfs/api/v1.1/files/attachments': lambda data: set_attachments(data),
            '/psbfs/api/v2/dossier': lambda data: set_credit_info(data),
            '/api/integration/documents/search': lambda data: get_documents(data),
            '/psbfs/api/v1.1/jobs/package': lambda data: create_archive(data)
        },
        'PUT': {
        },
        'DELETE': {
        }
    }
    
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
        """Парсит multipart/form-data запрос"""
        content_type = self.headers.get('Content-Type', '')
        
        if not content_type.startswith('multipart/form-data'):
            return None
        
        try:
            # Используем cgi для парсинга multipart данных
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST',
                        'CONTENT_TYPE': self.headers['Content-Type']}
            )
            
            result = {
                'fields': {},  # Текстовые поля
                'files': {}    # Файлы
            }
            
            for field in form.keys():
                field_item = form[field]
                
                if field_item.filename:
                    # Это файл
                    result['files'][field] = {
                        'filename': field_item.filename,
                        'content': field_item.file.read(),
                        'type': field_item.type
                    }
                else:
                    # Это текстовое поле
                    result['fields'][field] = field_item.value
            
            return result
            
        except Exception as e:
            print(f"Error parsing multipart: {e}")
            return None
    
    def _parse_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if not content_length:
            return None
        
        content_type = self.headers.get('Content-Type', '')
        
        # Обработка multipart/form-data
        if content_type.startswith('multipart/form-data'):
            return self._parse_multipart()
        
        # Обработка JSON
        elif content_type.startswith('application/json'):
            body = self.rfile.read(content_length)
            return json.loads(body.decode('utf-8'))
        
        # Обработка обычных бинарных данных
        else:
            return self.rfile.read(content_length)
    
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
        parsed = urlparse(path)
        clean_path = parsed.path
        query_params = parse_qs(parsed.query)
        
        # Сначала ищем точное совпадение
        handler = self.endpoints.get(method, {}).get(clean_path)
        
        if handler:
            try:
                if method in ['POST', 'PUT']:
                    data = self._parse_body()
                    result = handler(data)
                else:
                    import inspect
                    if inspect.signature(handler).parameters:
                        result = handler(query_params)
                    else:
                        result = handler()
                
                self._send_response(result)
                return
            except Exception as e:
                self._send_response({'error': str(e)}, 500)
                return
        
        # Если не нашли точное совпадение, ищем по regex паттернам
        for pattern, pattern_handler in self.endpoints.get(method, {}).items():
            if pattern.startswith('^'):  # Это regex паттерн
                import re
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
        pass

def run_server(port=8000, host='localhost'):
    server_address = (host, port)
    httpd = HTTPServer(server_address, MockHandler)
    
    print(f"🚀 Мок-сервер запущен на http://{host}:{port}")
    print("\n📡 Доступные эндпоинты:")
    print("    GET   /psbfs/api/v1.1/files/{id}/binaries")
    print("    GET   /api/integration/products/{clientId}")
    print("    GET   /psbfs/api/v1.1/jobs/package/{jobId}/binaries")
    print("    GET   /api/v1/ul/clients")
    print("    POST  /psbfs/api/v1.1/files/attachments")
    print("    POST  /psbfs/api/v2/dossier")
    print("    POST  /api/integration/documents/search")
    print("    POST  /psbfs/api/v1.1/jobs/package")
    
    print("\n💡 Для остановки сервера нажмите Ctrl+C")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")
        httpd.server_close()

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    host = sys.argv[2] if len(sys.argv) > 2 else 'localhost'
    
    run_server(port, host)
