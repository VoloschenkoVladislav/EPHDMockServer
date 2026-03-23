import time
import random
import threading
import uuid
from functools import wraps
from datetime import datetime, timedelta
from http import HTTPStatus

class UnavailabilitySimulator:
    """Класс для управления эмуляцией недоступности"""
    
    def __init__(self):
        self.stats = {
            'total_requests': 0,
            'failed_requests': 0,
            'circuit_breaker_open': False,
            'last_failure': None,
            'maintenance_mode': False,
            'maintenance_until': None
        }
        self.lock = threading.Lock()
    
    def get_stats(self):
        """Возвращает статистику"""
        with self.lock:
            return self.stats.copy()
    
    def reset_stats(self):
        """Сбрасывает статистику"""
        with self.lock:
            self.stats = {
                'total_requests': 0,
                'failed_requests': 0,
                'circuit_breaker_open': False,
                'last_failure': None,
                'maintenance_mode': False,
                'maintenance_until': None
            }
    
    def set_maintenance(self, duration_seconds=3600):
        """Включает режим обслуживания"""
        with self.lock:
            self.stats['maintenance_mode'] = True
            self.stats['maintenance_until'] = datetime.now() + timedelta(seconds=duration_seconds)
    
    def disable_maintenance(self):
        """Выключает режим обслуживания"""
        with self.lock:
            self.stats['maintenance_mode'] = False
            self.stats['maintenance_until'] = None

# Создаем глобальный экземпляр симулятора
unavailability_simulator = UnavailabilitySimulator()

def simulate_server_issues(
    mode='random',
    # Параметры для разных режимов
    failure_rate=0.2,
    error_code=503,
    error_message="Service Unavailable",
    min_delay=1,
    max_delay=10,
    timeout_seconds=30,
    circuit_breaker_threshold=5,
    circuit_breaker_timeout=60,
    # Дополнительные опции
    add_retry_after=True,
    add_debug_headers=True,
    exclude_paths=None  # Пути, которые не должны эмулировать ошибки
):
    """
    Универсальный декоратор для эмуляции проблем с сервером
    
    Режимы:
    - random: случайные ошибки
    - always: всегда ошибка
    - never: никогда ошибка (отключает эмуляцию)
    - timeout: эмуляция таймаута
    - slow: медленные ответы
    - circuit_breaker: circuit breaker pattern
    - maintenance: режим обслуживания
    - burst: периодические всплески ошибок
    - rate_limit: эмуляция rate limiting
    - intermittent: перемежающиеся ошибки
    """
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Получаем путь из request если доступен
            request_path = None
            if args and hasattr(args[0], 'path'):
                request_path = args[0].path
            
            # Проверяем исключенные пути
            if exclude_paths and request_path in exclude_paths:
                return func(*args, **kwargs)
            
            # Обновляем статистику
            with unavailability_simulator.lock:
                unavailability_simulator.stats['total_requests'] += 1
            
            current_mode = mode() if callable(mode) else mode
            
            # Режим "никогда"
            if current_mode == 'never':
                return func(*args, **kwargs)
            
            # Режим обслуживания
            if current_mode == 'maintenance' or unavailability_simulator.stats['maintenance_mode']:
                if unavailability_simulator.stats['maintenance_until']:
                    if datetime.now() < unavailability_simulator.stats['maintenance_until']:
                        return _generate_maintenance_response(
                            unavailability_simulator.stats['maintenance_until']
                        )
                    else:
                        unavailability_simulator.stats['maintenance_mode'] = False
            
            # Rate limiting режим
            if current_mode == 'rate_limit':
                # Простая эмуляция rate limiting (каждый 5-й запрос)
                if unavailability_simulator.stats['total_requests'] % 5 == 0:
                    with unavailability_simulator.lock:
                        unavailability_simulator.stats['failed_requests'] += 1
                    return _generate_error_response(
                        429,
                        "Too Many Requests - rate limit exceeded",
                        retry_after=30
                    )
            
            # Burst режим (периодические всплески)
            if current_mode == 'burst':
                # Каждые 10 запросов - серия ошибок
                cycle = unavailability_simulator.stats['total_requests'] % 20
                if 5 <= cycle <= 8:  # Всплеск ошибок
                    with unavailability_simulator.lock:
                        unavailability_simulator.stats['failed_requests'] += 1
                    return _generate_error_response(
                        error_code,
                        f"Burst error - service unstable (cycle {cycle})"
                    )
            
            # Intermittent режим (перемежающиеся ошибки)
            if current_mode == 'intermittent':
                # Ошибки появляются и исчезают
                if int(time.time()) % 30 < 15:  # 15 секунд ошибок, 15 секунд нормы
                    if random.random() < 0.7:  # 70% ошибок в "плохой" период
                        with unavailability_simulator.lock:
                            unavailability_simulator.stats['failed_requests'] += 1
                        return _generate_error_response(
                            error_code,
                            "Intermittent service disruption"
                        )
            
            # Обработка circuit breaker
            if current_mode == 'circuit_breaker':
                if unavailability_simulator.stats['circuit_breaker_open']:
                    return _generate_error_response(
                        503,
                        "Circuit breaker is OPEN - service unavailable",
                        retry_after=circuit_breaker_timeout if add_retry_after else None
                    )
            
            # Случайные ошибки
            if current_mode == 'random' and random.random() < failure_rate:
                with unavailability_simulator.lock:
                    unavailability_simulator.stats['failed_requests'] += 1
                    unavailability_simulator.stats['last_failure'] = datetime.now()
                    
                    # Обновляем circuit breaker
                    if unavailability_simulator.stats['failed_requests'] >= circuit_breaker_threshold:
                        unavailability_simulator.stats['circuit_breaker_open'] = True
                
                return _generate_error_response(
                    error_code,
                    error_message,
                    retry_after=random.randint(10, 60) if add_retry_after else None
                )
            
            # Всегда ошибка
            if current_mode == 'always':
                with unavailability_simulator.lock:
                    unavailability_simulator.stats['failed_requests'] += 1
                return _generate_error_response(error_code, error_message)
            
            # Таймаут
            if current_mode == 'timeout':
                print(f"⏰ Эмуляция таймаута: запрос завис на {timeout_seconds}с")
                time.sleep(timeout_seconds + 5)  # Больше чем таймаут клиента
                return _generate_error_response(504, "Gateway Timeout")
            
            # Медленный ответ
            if current_mode == 'slow':
                delay = random.uniform(min_delay, max_delay)
                print(f"🐌 Медленный ответ: задержка {delay:.2f}с")
                time.sleep(delay)
            
            # Выполняем оригинальную функцию
            result = func(*args, **kwargs)
            
            # Сбрасываем circuit breaker при успехе
            if current_mode == 'circuit_breaker' and unavailability_simulator.stats['circuit_breaker_open']:
                with unavailability_simulator.lock:
                    unavailability_simulator.stats['circuit_breaker_open'] = False
                    unavailability_simulator.stats['failed_requests'] = 0
            
            # Добавляем debug заголовки
            if add_debug_headers and isinstance(result, tuple) and len(result) >= 2:
                data, status = result[0], result[1]
                headers = result[2] if len(result) > 2 else {}
                headers['X-Unavailability-Mode'] = current_mode
                headers['X-Request-Id'] = str(random.randint(1000, 9999))
                return (data, status, headers)
            
            return result
        
        return wrapper
    return decorator

def _generate_maintenance_response(maintenance_until):
    """Генерирует ответ о плановом обслуживании"""
    return ({
        'status': 'ERROR',
        'error': {
            'code': 503,
            'message': 'Server is under maintenance',
            'maintenance_until': maintenance_until.isoformat(),
            'estimated_downtime_seconds': (maintenance_until - datetime.now()).total_seconds()
        }
    }, HTTPStatus.SERVICE_UNAVAILABLE, {
        'Retry-After': str(int((maintenance_until - datetime.now()).total_seconds())),
        'X-Maintenance-Mode': 'true'
    })

def _generate_error_response(code, message, retry_after=None):
    """Генерирует ответ с ошибкой"""
    response = {
        'status': 'ERROR',
        'error': {
            'code': code,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'request_id': str(uuid.uuid4())[:8]
        }
    }
    
    headers = {}
    if retry_after:
        headers['Retry-After'] = str(retry_after)
    
    status_map = {
        503: HTTPStatus.SERVICE_UNAVAILABLE,
        504: HTTPStatus.GATEWAY_TIMEOUT,
        500: HTTPStatus.INTERNAL_SERVER_ERROR,
        502: HTTPStatus.BAD_GATEWAY,
        429: HTTPStatus.TOO_MANY_REQUESTS
    }
    
    return (response, status_map.get(code, HTTPStatus.SERVICE_UNAVAILABLE), headers)