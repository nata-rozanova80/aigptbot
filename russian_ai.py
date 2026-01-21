"""
Класс для работы с российскими AI провайдерами:
- YandexGPT
- GigaChat (SberAI)
"""

import os
import requests
import logging
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class RussianAI:
    """Класс для работы с российскими AI провайдерами"""

    def __init__(self, provider='yandex'):
        """
        Инициализация AI-ассистента

        Args:
            provider (str): Провайдер AI ('yandex' или 'sber')
        """
        self.dialog_history = []
        self.provider = provider
        self._setup_provider()
        logger.info(f"🤖 RussianAI инициализирован с провайдером: {self.provider}")

    def _setup_provider(self):
        """Настройка параметров выбранного провайдера"""
        if self.provider == 'yandex':
            self.folder_id = os.getenv('YANDEX_FOLDER_ID')
            self.api_key = os.getenv('YANDEX_API_KEY')
            self.model = os.getenv('YANDEX_MODEL', 'yandexgpt-lite')
            self.url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'

            if not self.folder_id or not self.api_key:
                logger.error("❌ Отсутствуют YANDEX_FOLDER_ID или YANDEX_API_KEY")
                raise ValueError(
                    "Необходимо указать YANDEX_FOLDER_ID и YANDEX_API_KEY в .env файле"
                )

            logger.info(f"✅ YandexGPT настроен: модель={self.model}")

        elif self.provider == 'sber':
            self.auth_data = os.getenv('SBER_AUTH_DATA')
            self.url = 'https://gigachat.devices.sberbank.ru/api/v1/chat/completions'

            if not self.auth_data:
                logger.warning("⚠️ Отсутствует SBER_AUTH_DATA")

            logger.info("✅ GigaChat настроен")

        else:
            raise ValueError(f"❌ Неподдерживаемый провайдер: {self.provider}")

    def set_provider(self, provider):
        """
        Сменить AI провайдера

        Args:
            provider (str): Новый провайдер ('yandex' или 'sber')
        """
        if provider not in ['yandex', 'sber']:
            raise ValueError(f"❌ Неподдерживаемый провайдер: {provider}")

        logger.info(f"🔄 Смена провайдера: {self.provider} → {provider}")
        self.provider = provider
        self._setup_provider()
        self.clear_history()

    def add_message(self, role, text):
        """
        Добавить сообщение в историю диалога

        Args:
            role (str): Роль отправителя ('user' или 'assistant')
            text (str): Текст сообщения
        """
        self.dialog_history.append({
            'role': role,
            'text': text
        })
        logger.debug(f"💬 Добавлено сообщение [{role}]: {text[:50]}...")

    def clear_history(self):
        """Очистить историю диалога"""
        messages_count = len(self.dialog_history)
        self.dialog_history = []
        logger.info(f"🗑 История диалога очищена (было {messages_count} сообщений)")

    def generate_response(self, user_message):
        """
        Сгенерировать ответ на сообщение пользователя

        Args:
            user_message (str): Сообщение от пользователя

        Returns:
            str: Ответ от AI
        """
        self.add_message('user', user_message)

        try:
            if self.provider == 'yandex':
                response = self._yandex_request()
            elif self.provider == 'sber':
                response = self._sber_request()
            else:
                return "❌ Ошибка: неподдерживаемый провайдер"

            if response:
                self.add_message('assistant', response)
                return response
            else:
                return "❌ Не удалось получить ответ от AI"

        except Exception as e:
            logger.error(f"❌ Ошибка генерации ответа: {e}")
            return f"❌ Произошла ошибка: {str(e)}"

    def _yandex_request(self):
        """
        Отправить запрос к YandexGPT API

        Returns:
            str: Ответ от YandexGPT или None в случае ошибки
        """
        headers = {
            'Authorization': f'Api-Key {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Формируем сообщения для Yandex API
        messages = []
        for msg in self.dialog_history:
            messages.append({
                'role': msg['role'],
                'text': msg['text']
            })

        payload = {
            'modelUri': f'gpt://{self.folder_id}/{self.model}',
            'completionOptions': {
                'stream': False,
                'temperature': 0.6,
                'maxTokens': 2000
            },
            'messages': messages
        }

        logger.info(f"📤 Отправка запроса к YandexGPT ({len(messages)} сообщений)")

        try:
            response = requests.post(
                self.url,
                headers=headers,
                json=payload,
                timeout=30
            )

            logger.info(f"📥 Ответ YandexGPT: status={response.status_code}")

            if response.status_code == 200:
                data = response.json()
                result_text = data['result']['alternatives'][0]['message']['text']
                logger.info(f"✅ Успешный ответ от YandexGPT ({len(result_text)} символов)")
                return result_text

            elif response.status_code == 401:
                error_msg = "❌ Ошибка 401: Неверный API ключ"
                logger.error(error_msg)
                return error_msg

            elif response.status_code == 403:
                error_msg = (
                    "❌ Ошибка 403: Доступ запрещен\n"
                    "Проверьте:\n"
                    "• Активен ли биллинг\n"
                    "• Назначена ли роль ai.languageModels.user\n"
                    "• Правильность FOLDER_ID"
                )
                logger.error(error_msg)
                return error_msg

            else:
                error_text = response.text
                error_msg = f"❌ Ошибка YandexGPT: {response.status_code}\n{error_text[:200]}"
                logger.error(error_msg)
                return error_msg

        except requests.exceptions.Timeout:
            error_msg = "⏱ Превышено время ожидания ответа от YandexGPT"
            logger.error(error_msg)
            return error_msg

        except requests.exceptions.ConnectionError:
            error_msg = "🌐 Ошибка соединения с YandexGPT"
            logger.error(error_msg)
            return error_msg

        except Exception as e:
            error_msg = f"❌ Неожиданная ошибка: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _sber_request(self):
        """
        Отправить запрос к GigaChat (SberAI) API

        Returns:
            str: Ответ от GigaChat или None в случае ошибки
        """
        if not self.auth_data:
            return "❌ Не указан SBER_AUTH_DATA в .env файле"

        headers = {
            'Authorization': f'Bearer {self.auth_data}',
            'Content-Type': 'application/json'
        }

        # Формируем сообщения для GigaChat API
        messages = []
        for msg in self.dialog_history:
            messages.append({
                'role': msg['role'],
                'content': msg['text']
            })

        payload = {
            'model': 'GigaChat',
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 2000
        }

        logger.info(f"📤 Отправка запроса к GigaChat ({len(messages)} сообщений)")

        try:
            response = requests.post(
                self.url,
                headers=headers,
                json=payload,
                timeout=30,
                verify=False  # Для GigaChat может потребоваться отключить проверку SSL
            )

            logger.info(f"📥 Ответ GigaChat: status={response.status_code}")

            if response.status_code == 200:
                data = response.json()
                result_text = data['choices'][0]['message']['content']
                logger.info(f"✅ Успешный ответ от GigaChat ({len(result_text)} символов)")
                return result_text
            else:
                error_msg = f"❌ Ошибка GigaChat: {response.status_code}"
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ Ошибка запроса к GigaChat: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def get_history_length(self):
        """
        Получить количество сообщений в истории

        Returns:
            int: Количество сообщений
        """
        return len(self.dialog_history)
