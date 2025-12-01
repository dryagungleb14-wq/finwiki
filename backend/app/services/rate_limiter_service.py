"""
Rate Limiter для Gemini API
- Управление лимитами RPM (requests per minute)
- Очередь запросов
- Retry logic с exponential backoff
"""
import time
import threading
from queue import Queue, Empty
from concurrent.futures import Future
from typing import Any, Callable
import logging

logger = logging.getLogger(__name__)


class GeminiRateLimiter:
    """
    Rate limiter для Gemini API с поддержкой очереди запросов

    Лимиты Gemini 2.0 Flash (free tier):
    - 10 RPM (requests per minute)
    - 250 RPD (requests per day)
    """

    def __init__(self, rpm: int = 10, max_retries: int = 3):
        """
        Args:
            rpm: максимальное количество запросов в минуту
            max_retries: максимальное количество повторных попыток
        """
        self.rpm = rpm
        self.max_retries = max_retries
        self.min_interval = 60.0 / rpm  # секунд между запросами
        self.queue = Queue()
        self.lock = threading.Lock()
        self.last_request_time = 0
        self.request_count = 0
        self.daily_count = 0
        self.last_reset_time = time.time()

        # Запускаем worker thread
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

        logger.info(f"✅ Gemini Rate Limiter initialized: {rpm} RPM")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Выполнить функцию с соблюдением rate limits

        Args:
            func: функция для вызова (обычно Gemini API call)
            *args, **kwargs: аргументы функции

        Returns:
            результат выполнения функции

        Raises:
            Exception: если все retry попытки исчерпаны
        """
        future = Future()
        self.queue.put((func, args, kwargs, future, 0))  # 0 = retry_count

        # Ждем результата (с timeout 60 секунд)
        try:
            return future.result(timeout=60)
        except Exception as e:
            logger.error(f"❌ Rate limiter call failed: {e}")
            raise

    def _process_queue(self):
        """
        Worker thread для обработки очереди запросов
        """
        while True:
            try:
                # Получаем задачу из очереди (блокирующий вызов)
                func, args, kwargs, future, retry_count = self.queue.get(timeout=1)

                # Проверяем rate limit
                self._wait_for_rate_limit()

                # Выполняем запрос
                try:
                    result = func(*args, **kwargs)
                    future.set_result(result)
                    self.request_count += 1
                    self.daily_count += 1

                    logger.debug(f"✅ Request successful. Total today: {self.daily_count}")

                except Exception as e:
                    # Retry logic
                    if retry_count < self.max_retries:
                        retry_count += 1
                        wait_time = 2 ** retry_count  # Exponential backoff: 2s, 4s, 8s

                        logger.warning(
                            f"⚠️  Request failed (attempt {retry_count}/{self.max_retries}). "
                            f"Retrying in {wait_time}s... Error: {e}"
                        )

                        time.sleep(wait_time)

                        # Возвращаем в очередь для повтора
                        self.queue.put((func, args, kwargs, future, retry_count))
                    else:
                        # Исчерпаны все попытки
                        logger.error(f"❌ Request failed after {self.max_retries} retries: {e}")
                        future.set_exception(e)

            except Empty:
                # Очередь пуста, продолжаем
                continue
            except Exception as e:
                logger.error(f"❌ Queue processing error: {e}")

    def _wait_for_rate_limit(self):
        """
        Ждать если нужно для соблюдения rate limit
        """
        with self.lock:
            current_time = time.time()

            # Сбросить счетчик если прошла минута
            if current_time - self.last_reset_time >= 60:
                self.request_count = 0
                self.last_reset_time = current_time

            # Проверить интервал между запросами
            time_since_last = current_time - self.last_request_time

            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                logger.debug(f"⏳ Rate limit: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)

            self.last_request_time = time.time()

    def get_stats(self) -> dict:
        """
        Получить статистику использования
        """
        return {
            "rpm_limit": self.rpm,
            "requests_last_minute": self.request_count,
            "requests_today": self.daily_count,
            "queue_size": self.queue.qsize(),
            "min_interval_sec": self.min_interval
        }


# Глобальный rate limiter (singleton)
# Используется для всех Gemini API calls
_global_limiter = None


def get_rate_limiter(rpm: int = 10) -> GeminiRateLimiter:
    """
    Получить глобальный rate limiter (singleton)
    """
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = GeminiRateLimiter(rpm=rpm)
    return _global_limiter


# Пример использования
if __name__ == "__main__":
    import google.generativeai as genai

    # Настройка логирования
    logging.basicConfig(level=logging.DEBUG)

    # Инициализация Gemini
    genai.configure(api_key="YOUR_API_KEY")
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    # Получаем rate limiter
    limiter = get_rate_limiter(rpm=10)

    # Тестовые запросы
    for i in range(5):
        def make_request():
            response = model.generate_content("Привет! Как дела?")
            return response.text

        try:
            result = limiter.call(make_request)
            print(f"Request {i+1}: {result[:50]}...")
        except Exception as e:
            print(f"Request {i+1} failed: {e}")

    # Статистика
    stats = limiter.get_stats()
    print(f"\nStats: {stats}")
