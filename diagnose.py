import os
import requests
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🔍 ДИАГНОСТИКА YANDEX CLOUD API")
print("=" * 70)

# Проверка переменных окружения
FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
API_KEY = os.getenv('YANDEX_API_KEY')

print("\n📋 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
print("-" * 70)

if not FOLDER_ID:
    print("❌ YANDEX_FOLDER_ID не найден в .env")
else:
    print(f"✅ YANDEX_FOLDER_ID: {FOLDER_ID[:10]}...{FOLDER_ID[-5:]}")
    print(f"   Длина: {len(FOLDER_ID)} символов")

if not API_KEY:
    print("❌ YANDEX_API_KEY не найден в .env")
else:
    print(f"✅ YANDEX_API_KEY: {API_KEY[:10]}...{API_KEY[-5:]}")
    print(f"   Длина: {len(API_KEY)} символов")

if not FOLDER_ID or not API_KEY:
    print("\n❌ Не все переменные окружения настроены!")
    exit(1)

# Тест запроса к API
print("\n🔗 ТЕСТОВЫЙ ЗАПРОС К YANDEX API:")
print("-" * 70)

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
        "maxTokens": 100
    },
    "messages": [
        {"role": "user", "text": "Привет!"}
    ]
}

print(f"URL: {url}")
print(f"Model URI: gpt://{FOLDER_ID}/yandexgpt-lite")

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)

    print(f"\n📊 РЕЗУЛЬТАТ ЗАПРОСА:")
    print(f"Статус код: {response.status_code}")

    if response.status_code == 200:
        print("✅ УСПЕХ! API работает!")
        data = response.json()
        print(f"\nОтвет: {data}")

    elif response.status_code == 400:
        print("❌ ОШИБКА 400: Неверный запрос")
        print(f"Детали: {response.text}")
        print("\n💡 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print("   - Неправильный формат modelUri")
        print("   - Неправильный FOLDER_ID")

    elif response.status_code == 401:
        print("❌ ОШИБКА 401: Неверная авторизация")
        print(f"Детали: {response.text}")
        print("\n💡 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print("   - Неверный API_KEY")
        print("   - API_KEY истек")

    elif response.status_code == 403:
        print("❌ ОШИБКА 403: Доступ запрещен")
        print(f"Детали: {response.text}")
        print("\n💡 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print("   1. У сервисного аккаунта нет роли 'ai.languageModels.user'")
        print("   2. Биллинг-аккаунт не активирован")
        print("   3. FOLDER_ID не принадлежит вашему аккаунту")
        print("   4. API-ключ создан для другого аккаунта")

        print("\n🔧 ЧТО ДЕЛАТЬ:")
        print("   1. Откройте: https://console.cloud.yandex.ru")
        print("   2. Перейдите в ваш каталог")
        print("   3. Сервисные аккаунты → Выберите аккаунт")
        print("   4. Права доступа → Убедитесь что есть 'ai.languageModels.user'")
        print("   5. Биллинг → Проверьте что аккаунт активен")

    elif response.status_code == 429:
        print("❌ ОШИБКА 429: Превышен лимит запросов")
        print(f"Детали: {response.text}")

    else:
        print(f"❌ НЕОЖИДАННАЯ ОШИБКА: {response.status_code}")
        print(f"Детали: {response.text}")

except requests.exceptions.ConnectionError:
    print("❌ ОШИБКА ПОДКЛЮЧЕНИЯ")
    print("Проверьте интернет-соединение")

except requests.exceptions.Timeout:
    print("❌ ПРЕВЫШЕНО ВРЕМЯ ОЖИДАНИЯ")
    print("Сервер не отвечает")

except Exception as e:
    print(f"❌ НЕОЖИДАННАЯ ОШИБКА: {e}")

print("\n" + "=" * 70)
