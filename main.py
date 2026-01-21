# main.py
# AI-ассистент с поддержкой YandexGPT и GigaChat

import os
import json
import logging
import requests
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
# Настраиваем вывод логов для отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ========== КЛАСС ДЛЯ РАБОТЫ С РОССИЙСКИМИ AI ==========

class RussianAI:
    """
    Класс для работы с российскими нейросетями:
    - YandexGPT (Яндекс)
    - GigaChat (Сбер)

    Управляет историей диалога и генерацией ответов
    """

    def __init__(self, provider=None):
        """
        Конструктор класса

        Args:
            provider (str): Название провайдера ('yandex' или 'gigachat')
                           Если не указан - берется из переменных окружения
        """
        # Получаем провайдера из параметра или из .env
        self.provider = provider or os.getenv('DEFAULT_PROVIDER', 'yandex')

        # Инициализация истории диалога как пустого списка
        # Каждое сообщение будет добавляться в этот список
        self.history = []

        # Настройка выбранного провайдера (загрузка параметров)
        self.set_provider(self.provider)

        logger.info(f"✅ RussianAI инициализирован с провайдером: {self.provider}")

    # ========== МЕТОД ДЛЯ ПЕРЕКЛЮЧЕНИЯ ПРОВАЙДЕРА ==========

    def set_provider(self, provider_name):
        """
        Переключение между разными провайдерами AI

        Args:
            provider_name (str): 'yandex' или 'gigachat'
        """
        self.provider = provider_name.lower()

        if self.provider == 'yandex':
            self._setup_yandex()
        elif self.provider == 'gigachat':
            self._setup_gigachat()
        else:
            raise ValueError(f"Неизвестный провайдер: {provider_name}")

        logger.info(f"🔄 Провайдер изменен на: {self.provider}")

    # ========== НАСТРОЙКА YANDEXGPT ==========

    def _setup_yandex(self):
        """
        Настройка параметров для YandexGPT
        """
        # Загружаем параметры из переменных окружения
        self.folder_id = os.getenv('YANDEX_FOLDER_ID')
        self.api_key = os.getenv('YANDEX_API_KEY')
        self.model = os.getenv('YANDEX_MODEL', 'yandexgpt-lite')

        # Проверка наличия обязательных параметров
        if not self.folder_id or not self.api_key:
            raise ValueError(
                "❌ Не указаны YANDEX_FOLDER_ID или YANDEX_API_KEY в .env файле"
            )

        # URL для API YandexGPT
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

        # Заголовки для запроса
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_key}",
            "x-folder-id": self.folder_id
        }

        logger.info(f"🔧 YandexGPT настроен: модель={self.model}")

    # ========== НАСТРОЙКА GIGACHAT ==========

    def _setup_gigachat(self):
        """
        Настройка параметров для GigaChat (Сбер)
        """
        # Загружаем параметры из переменных окружения
        self.auth_data = os.getenv('SBER_AUTH')
        self.model = os.getenv('GIGACHAT_MODEL', 'GigaChat:latest')

        # Проверка наличия авторизационных данных
        if not self.auth_data:
            raise ValueError(
                "❌ Не указан SBER_AUTH в .env файле для GigaChat"
            )

        # URL для API GigaChat
        self.api_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

        # Сначала получаем access_token
        self._get_gigachat_token()

        logger.info(f"🔧 GigaChat настроен: модель={self.model}")

    def _get_gigachat_token(self):
        """
        Получение токена доступа для GigaChat
        (Токен обновляется периодически)
        """
        token_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

        headers = {
            "Authorization": f"Basic {self.auth_data}",
            "RqUID": "your-unique-request-id",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {"scope": "GIGACHAT_API_PERS"}

        try:
            response = requests.post(
                token_url,
                headers=headers,
                data=data,
                verify=False,  # Отключение проверки SSL (для Сбера)
                timeout=10
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']

                # Обновляем заголовки с новым токеном
                self.headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                logger.info("✅ GigaChat токен получен успешно")
            else:
                raise Exception(f"Ошибка получения токена: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Ошибка при получении токена GigaChat: {e}")
            raise

    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С ИСТОРИЕЙ ДИАЛОГА ==========

    def add_message(self, role, content):
        """
        Добавление сообщения в историю диалога

        Args:
            role (str): Роль отправителя ('user' или 'assistant')
            content (str): Текст сообщения
        """
        message = {
            "role": role,
            "text": content
        }
        self.history.append(message)
        logger.info(f"💬 Добавлено сообщение: {role}")

    def clear_history(self):
        """
        Очистка истории диалога
        Полезно для начала нового разговора
        """
        self.history = []
        logger.info("🗑️ История диалога очищена")

    def get_history(self):
        """
        Получение текущей истории диалога

        Returns:
            list: Список сообщений
        """
        return self.history

    # ========== ГЛАВНЫЙ МЕТОД ГЕНЕРАЦИИ ОТВЕТА ==========

    def generate_response(self, user_message):
        """
        Генерация ответа на сообщение пользователя

        Args:
            user_message (str): Сообщение от пользователя

        Returns:
            str: Ответ от AI или сообщение об ошибке
        """
        # Добавляем сообщение пользователя в историю
        self.add_message("user", user_message)

        try:
            # Выбираем провайдера и вызываем соответствующий метод
            if self.provider == 'yandex':
                response_text = self._yandex_request()
            elif self.provider == 'gigachat':
                response_text = self._gigachat_request()
            else:
                response_text = "❌ Неизвестный провайдер AI"

            # Добавляем ответ AI в историю
            if response_text and not response_text.startswith("❌"):
                self.add_message("assistant", response_text)

            return response_text

        except Exception as e:
            error_message = f"❌ Ошибка генерации ответа: {str(e)}"
            logger.error(error_message)
            return error_message

    # ========== ФУНКЦИЯ ДЛЯ РАБОТЫ С YANDEXGPT ==========

    def _yandex_request(self):
        """
        Отправка запроса к YandexGPT и получение ответа

        Returns:
            str: Ответ от YandexGPT или сообщение об ошибке
        """
        # Формируем тело запроса
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{self.model}",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,  # Креативность ответа (0-1)
                "maxTokens": 2000  # Максимальная длина ответа
            },
            "messages": self.history
        }

        try:
            logger.info("📡 Отправка запроса к YandexGPT...")

            # Отправляем POST-запрос к API
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            # Проверяем статус ответа
            if response.status_code == 200:
                data = response.json()

                # Извлекаем текст ответа
                if 'result' in data and 'alternatives' in data['result']:
                    alternatives = data['result']['alternatives']
                    if alternatives and 'message' in alternatives[0]:
                        answer = alternatives[0]['message']['text']
                        logger.info(f"✅ Получен ответ от YandexGPT ({len(answer)} символов)")
                        return answer
                    else:
                        return "❌ Неожиданный формат ответа от YandexGPT"
                else:
                    return "❌ Ошибка в структуре ответа YandexGPT"

            elif response.status_code == 401:
                return "❌ Ошибка авторизации YandexGPT. Проверьте API-ключ."

            elif response.status_code == 403:
                return "❌ Доступ запрещен. Проверьте права доступа в Yandex Cloud."

            elif response.status_code == 429:
                return "❌ Превышен лимит запросов. Попробуйте позже."

            else:
                error_msg = f"❌ Ошибка YandexGPT: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f"\n{error_data['error']}"
                except:
                    pass
                logger.error(error_msg)
                return error_msg

        except requests.exceptions.Timeout:
            return "❌ Превышено время ожидания ответа от YandexGPT"

        except requests.exceptions.ConnectionError:
            return "❌ Ошибка подключения к YandexGPT"

        except Exception as e:
            error_msg = f"❌ Неожиданная ошибка YandexGPT: {str(e)}"
            logger.error(error_msg)
            return error_msg

    # ========== ФУНКЦИЯ ДЛЯ РАБОТЫ С GIGACHAT ==========

    def _gigachat_request(self):
        """
        Отправка запроса к GigaChat (Сбер) и получение ответа

        Returns:
            str: Ответ от GigaChat или сообщение об ошибке
        """
        # Преобразуем историю в формат GigaChat
        # GigaChat использует "role" вместо "role" в сообщениях
        messages = []
        for msg in self.history:
            messages.append({
                "role": msg["role"],
                "content": msg["text"]
            })

        # Формируем тело запроса
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
            "n": 1
        }

        try:
            logger.info("📡 Отправка запроса к GigaChat...")

            # Отправляем POST-запрос к API
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                verify=False,  # Отключение SSL для Сбера
                timeout=30
            )

            # Проверяем статус ответа
            if response.status_code == 200:
                data = response.json()

                # Извлекаем текст ответа
                if 'choices' in data and len(data['choices']) > 0:
                    answer = data['choices'][0]['message']['content']
                    logger.info(f"✅ Получен ответ от GigaChat ({len(answer)} символов)")
                    return answer
                else:
                    return "❌ Неожиданный формат ответа от GigaChat"

            elif response.status_code == 401:
                # Токен истек, пробуем обновить
                logger.warning("⚠️ Токен GigaChat истек, обновляю...")
                self._get_gigachat_token()
                return self._gigachat_request()  # Повторный запрос

            elif response.status_code == 429:
                return "❌ Превышен лимит запросов GigaChat. Попробуйте позже."

            else:
                error_msg = f"❌ Ошибка GigaChat: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f"\n{error_data['error']}"
                except:
                    pass
                logger.error(error_msg)
                return error_msg

        except requests.exceptions.Timeout:
            return "❌ Превышено время ожидания ответа от GigaChat"

        except requests.exceptions.ConnectionError:
            return "❌ Ошибка подключения к GigaChat"

        except Exception as e:
            error_msg = f"❌ Неожиданная ошибка GigaChat: {str(e)}"
            logger.error(error_msg)
            return error_msg


# ========== ФУНКЦИЯ ДЛЯ ТЕСТИРОВАНИЯ КЛАССА ==========

def test_russian_ai():
    """
    Простой тест для проверки работы класса RussianAI
    Используется для отладки без Telegram-бота
    """
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ КЛАССА RussianAI")
    print("=" * 60)

    try:
        # Создаем экземпляр класса
        ai = RussianAI(provider='yandex')
        print(f"\n✅ Класс инициализирован с провайдером: {ai.provider}")

        # Тестовый запрос
        test_message = "Привет! Расскажи о себе кратко."
        print(f"\n📝 Отправляем тестовое сообщение: '{test_message}'")

        # Получаем ответ
        response = ai.generate_response(test_message)
        print(f"\n🤖 Ответ AI:\n{response}")

        # Проверяем историю
        print(f"\n📊 Количество сообщений в истории: {len(ai.get_history())}")

        # Очистка истории
        ai.clear_history()
        print(f"✅ История очищена. Сообщений в истории: {len(ai.get_history())}")

        print("\n" + "=" * 60)
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ОШИБКА ПРИ ТЕСТИРОВАНИИ: {e}")
        print("\n💡 ПРОВЕРЬТЕ:")
        print("1. Файл .env создан и заполнен")
        print("2. API-ключи правильные")
        print("3. Интернет-соединение работает")


# ========== ТОЧКА ВХОДА ==========

if __name__ == '__main__':
    """
    Запуск тестирования класса
    В следующем уроке здесь будет запуск Telegram-бота
    """
    print("\n💡 ВАЖНО: Это тестовая версия класса")
    print("В следующем уроке мы добавим Telegram-бота\n")

    # Запускаем тест
    test_russian_ai()
