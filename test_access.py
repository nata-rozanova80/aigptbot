import os
import requests
from dotenv import load_dotenv

load_dotenv()

FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
API_KEY = os.getenv('YANDEX_API_KEY')

print("=" * 60)
print("🧪 ТЕСТ ДОСТУПА К YANDEXGPT")
print("=" * 60)

# Проверка переменных
print(f"\n✅ FOLDER_ID: {FOLDER_ID[:15]}...{FOLDER_ID[-5:]}")
print(f"✅ API_KEY: {API_KEY[:15]}...{API_KEY[-5:]}")

# Тестовый запрос
url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Api-Key {API_KEY}",
    "x-folder-id": FOLDER_ID
}

payload = {
    "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
    "completionOptions": {
        "stream": False,
        "temperature": 0.7,
        "maxTokens": 50
    },
    "messages": [
        {"role": "user", "text": "Скажи 'Привет!'"}
    ]
}

print("\n📡 Отправка запроса...")

response = requests.post(url, headers=headers, json=payload)

print(f"📊 Статус: {response.status_code}")

if response.status_code == 200:
    print("✅✅✅ УСПЕХ! API РАБОТАЕТ! ✅✅✅")
    data = response.json()
    answer = data['result']['alternatives'][0]['message']['text']
    print(f"\n🤖 Ответ: {answer}")

elif response.status_code == 400:
    print("❌ ОШИБКА 400: Неверный запрос")
    print("⚠️ Проверьте FOLDER_ID - возможно это ID облака, а не каталога")

elif response.status_code == 401:
    print("❌ ОШИБКА 401: Неверный API-ключ")
    print("⚠️ Создайте новый API-ключ")

elif response.status_code == 403:
    print("❌ ОШИБКА 403: Доступ запрещен")
    print("\n🔧 ПРИЧИНЫ:")
    print("1. ⚠️ Биллинг не активирован")
    print("2. ⚠️ Нет роли ai.languageModels.user")
    print("3. ⚠️ API-ключ создан для другого каталога")

elif response.status_code == 429:
    print("❌ ОШИБКА 429: Превышен лимит запросов")

else:
    print(f"❌ НЕОЖИДАННАЯ ОШИБКА: {response.status_code}")
    print(f"Детали: {response.text[:200]}")

print("\n" + "=" * 60)
