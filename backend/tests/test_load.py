from locust import HttpUser, task, between
import uuid
import logging

logger = logging.getLogger(__name__)

class MetricsUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://127.0.0.1:5000"  # Предполагаем, что бэкенд запущен на localhost:5000

    def on_start(self):
        """
        Регистрация пользователя и получение токена перед началом тестов.
        """
        # Используем статичный email для локаста (избегаем проблем с дублированием)
        email = "loadtest@example.com"
        password = "password123"
        
        self.token = None
        self.interview_id = None
        
        # Сначала пробуем регистрацию
        try:
            response = self.client.post(
                "/auth/register",
                json={"email": email, "password": password}
            )
            
            logger.info(f"Регистрация: статус {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.token = data.get("access_token")
                    if self.token:
                        logger.info("Токен получен при регистрации")
                    else:
                        logger.warning(f"access_token не найден в ответе: {data}")
                except Exception as e:
                    logger.error(f"Ошибка парсинга JSON: {e}")
            elif response.status_code == 400:
                # Email уже существует, пробуем логин
                logger.info("Email уже существует, пробуем логин")
                response = self.client.post(
                    "/auth/login",
                    json={"email": email, "password": password}
                )
                logger.info(f"Логин: статус {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.token = data.get("access_token")
                        if self.token:
                            logger.info("Токен получен при логине")
                        else:
                            logger.warning(f"access_token не найден при логине: {data}")
                    except Exception as e:
                        logger.error(f"Ошибка парсинга JSON при логине: {e}")
                else:
                    logger.error(f"Логин не удался: {response.text}")
            else:
                logger.error(f"Регистрация вернула статус {response.status_code}: {response.text}")
        
        except Exception as e:
            logger.error(f"Критическая ошибка при аутентификации: {e}")
        
        # Если получили токен, создаем интервью
        if self.token:
            self._create_interview()
    
    def _create_interview(self):
        """
        Создает интервью для получения valid interview_id.
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = self.client.post(
                "/interviews/start",
                json={"stack": "Python", "difficulty": "Средний"},
                headers=headers
            )
            
            logger.info(f"Создание интервью: статус {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.interview_id = data.get("interview_id")
                    if self.interview_id:
                        logger.info(f"Интервью создано: {self.interview_id}")
                    else:
                        logger.warning(f"interview_id не найден в ответе: {data}")
                except Exception as e:
                    logger.error(f"Ошибка парсинга JSON при создании интервью: {e}")
            else:
                logger.error(f"Создание интервью вернуло статус {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при создании интервью: {e}")

    @task
    def send_metrics(self):
        """
        Имитирует отправку метрик продукта.
        Создает новое интервью и отправляет метрики для него.
        """
        if not self.token:
            logger.warning("Токен не установлен, пропускаем отправку метрик")
            return
        
        # Создаем новое интервью перед каждой отправкой метрик
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Создаем интервью
            response = self.client.post(
                "/interviews/start",
                json={"stack": "Python", "difficulty": "Средний"},
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Ошибка создания интервью: {response.status_code}")
                return
            
            try:
                data = response.json()
                interview_id = data.get("interview_id")
                if not interview_id:
                    logger.error(f"interview_id не найден в ответе: {data}")
                    return
            except Exception as e:
                logger.error(f"Ошибка парсинга ответа интервью: {e}")
                return
            
            # Отправляем метрики для этого интервью
            response = self.client.post(
                "/metrics/submit",
                json={
                    "interview_id": interview_id,
                    "user_id": str(uuid.uuid4()),
                    "csat": 5,
                    "ces": 7,
                    "nps": 10,
                    "comment": "Отличный сервис!"
                },
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("Интервью создано и метрики отправлены успешно")
            else:
                logger.warning(f"Отправка метрик вернула статус {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Ошибка при отправке метрик: {e}")

# Как запустить этот нагрузочный тест:
# 1. Убедитесь, что ваш FastAPI бэкенд запущен.
# 2. Установите locust: pip install locust
# 3. Запустите locust из терминала в директории `backend`:
#    locust -f tests/test_load.py
# 4. Откройте браузер на http://localhost:8089 и запустите тест.
