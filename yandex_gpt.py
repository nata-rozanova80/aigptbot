"""
Модуль для работы с YandexGPT API
"""

import requests
import logging

logger = logging.getLogger(__name__)


class YandexGPT:
    """Класс для взаимодействия с YandexGPT API"""

    def __init__(self, api_key: str, folder_id: str):
        self.api_key = api_key
        self.folder_id = folder_id
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_key}"
        }

    def get_completion(self, messages: list, temperature: float = 0.6, max_tokens: int = 2000) -> str:
        data = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": max_tokens
            },
            "messages": messages
        }

        try:
            logger.info("📤 Отправка запроса к YandexGPT...")
            response = requests.post(self.url, json=data, headers=self.headers, timeout=30)

            if response.status_code == 200:
                result = response.json()
                answer = result['result']['alternatives'][0]['message']['text']
                logger.info("✅ Получен ответ от YandexGPT")
                return answer
            else:
                error_text = response.text
                logger.error(f"❌ Ошибка YandexGPT: {response.status_code} - {error_text}")
                return f"Ошибка API: {response.status_code}"

        except Exception as e:
            logger.error(f"❌ Ошибка при запросе к YandexGPT: {e}")
            return f"Произошла ошибка: {str(e)}"
