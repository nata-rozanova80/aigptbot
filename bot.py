#Telegram-бот AI-ассистент на базе российских нейросетей
"""
Telegram-бот AI-ассистент на базе российских нейросетей
Поддерживает YandexGPT и GigaChat (SberAI)
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters,
    CallbackContext
)
from russian_ai import RussianAI

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение токена бота из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError("❌ Не указан TELEGRAM_BOT_TOKEN в .env файле!")

# Глобальный словарь для хранения AI-ассистентов каждого пользователя
user_assistants = {}


def get_user_assistant(user_id):
    """
    Получить или создать AI-ассистента для конкретного пользователя

    Args:
        user_id (int): ID пользователя Telegram

    Returns:
        RussianAI: Экземпляр AI-ассистента
    """
    if user_id not in user_assistants:
        default_provider = os.getenv('DEFAULT_PROVIDER', 'yandex')
        user_assistants[user_id] = RussianAI(provider=default_provider)
        logger.info(f"🆕 Создан новый ассистент для пользователя {user_id}")
    return user_assistants[user_id]


def create_keyboard():
    """
    Создание inline-клавиатуры для управления ботом

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками управления
    """
    keyboard = [
        [
            InlineKeyboardButton("🟢 Yandex", callback_data='provider_yandex'),
            InlineKeyboardButton("🔵 Sber", callback_data='provider_sber')
        ],
        [
            InlineKeyboardButton("🗑 Очистить историю", callback_data='clear_history')
        ],
        [
            InlineKeyboardButton("ℹ️ Инфо", callback_data='info')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = user.id

    # Инициализируем ассистента для пользователя
    assistant = get_user_assistant(user_id)

    welcome_message = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я AI-ассистент на базе российских нейросетей.\n\n"
        f"🤖 *Текущий провайдер:* {assistant.provider.upper()}\n"
        f"💬 *Сообщений в истории:* {assistant.get_history_length()}\n\n"
        f"*Доступные команды:*\n"
        f"/start - Начать работу\n"
        f"/yandex - Переключиться на YandexGPT\n"
        f"/sber - Переключиться на GigaChat\n"
        f"/clear - Очистить историю диалога\n"
        f"/info - Информация о боте\n\n"
        f"Просто напиши мне что-нибудь, и я отвечу! 💬"
    )

    update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=create_keyboard()
    )
    logger.info(f"👤 Пользователь {user_id} ({user.first_name}) запустил бота")


def yandex_command(update: Update, context: CallbackContext):
    """Обработчик команды /yandex - переключение на YandexGPT"""
    user_id = update.effective_user.id
    assistant = get_user_assistant(user_id)

    try:
        assistant.set_provider('yandex')
        update.message.reply_text(
            "✅ Провайдер переключен на *YandexGPT*\n"
            "История диалога очищена.",
            parse_mode='Markdown',
            reply_markup=create_keyboard()
        )
        logger.info(f"🔄 Пользователь {user_id} переключился на Yandex")
    except Exception as e:
        update.message.reply_text(
            f"❌ Ошибка переключения: {str(e)}",
            reply_markup=create_keyboard()
        )
        logger.error(f"❌ Ошибка переключения на Yandex: {e}")


def sber_command(update: Update, context: CallbackContext):
    """Обработчик команды /sber - переключение на GigaChat"""
    user_id = update.effective_user.id
    assistant = get_user_assistant(user_id)

    try:
        assistant.set_provider('sber')
        update.message.reply_text(
            "✅ Провайдер переключен на *GigaChat (SberAI)*\n"
            "История диалога очищена.",
            parse_mode='Markdown',
            reply_markup=create_keyboard()
        )
        logger.info(f"🔄 Пользователь {user_id} переключился на Sber")
    except Exception as e:
        update.message.reply_text(
            f"❌ Ошибка переключения: {str(e)}",
            reply_markup=create_keyboard()
        )
        logger.error(f"❌ Ошибка переключения на Sber: {e}")


def clear_command(update: Update, context: CallbackContext):
    """Обработчик команды /clear - очистка истории диалога"""
    user_id = update.effective_user.id
    assistant = get_user_assistant(user_id)

    messages_before = assistant.get_history_length()
    assistant.clear_history()

    update.message.reply_text(
        f"🗑 История диалога очищена!\n"
        f"Удалено сообщений: {messages_before}\n\n"
        f"Можешь начать новый разговор.",
        reply_markup=create_keyboard()
    )
    logger.info(f"🗑 Пользователь {user_id} очистил историю ({messages_before} сообщений)")


def info_command(update: Update, context: CallbackContext):
    """Обработчик команды /info - информация о боте"""
    user_id = update.effective_user.id
    assistant = get_user_assistant(user_id)

    info_message = (
        "ℹ️ *Информация о боте*\n\n"
        f"🤖 *Текущий провайдер:* {assistant.provider.upper()}\n"
        f"💬 *Сообщений в истории:* {assistant.get_history_length()}\n\n"
        "*Поддерживаемые провайдеры:*\n"
        "• YandexGPT (Yandex Cloud)\n"
        "• GigaChat (SberAI)\n\n"
        "*Возможности:*\n"
        "✓ Ответы на вопросы\n"
        "✓ Генерация текста\n"
        "✓ Помощь в задачах\n"
        "✓ Сохранение контекста диалога\n\n"
        "*Разработчик:* ZeroCode University\n"
        "*Версия:* 1.0"
    )

    update.message.reply_text(
        info_message,
        parse_mode='Markdown',
        reply_markup=create_keyboard()
    )


def handle_message(update: Update, context: CallbackContext):
    """Обработчик текстовых сообщений от пользователя"""
    user_id = update.effective_user.id
    user_message = update.message.text

    # Получаем ассистента пользователя
    assistant = get_user_assistant(user_id)

    logger.info(f"💬 Получено сообщение от {user_id}: {user_message[:50]}...")

    # Отправляем индикатор "печатает..."
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action='typing'
    )

    try:
        # Генерируем ответ через AI
        response = assistant.generate_response(user_message)

        # Отправляем ответ пользователю
        update.message.reply_text(
            response,
            reply_markup=create_keyboard()
        )
        logger.info(f"✅ Отправлен ответ пользователю {user_id}")

    except Exception as e:
        error_message = (
            "❌ Произошла ошибка при генерации ответа.\n\n"
            f"*Детали:* {str(e)}\n\n"
            "*Попробуй:*\n"
            "• Проверить настройки API ключей в .env\n"
            "• Очистить историю командой /clear\n"
            "• Переключить провайдера (/yandex или /sber)"
        )
        update.message.reply_text(
            error_message,
            parse_mode='Markdown',
            reply_markup=create_keyboard()
        )
        logger.error(f"❌ Ошибка генерации ответа для {user_id}: {e}")


def button_callback(update: Update, context: CallbackContext):
    """Обработчик нажатий на inline-кнопки"""
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data

    # Подтверждаем получение callback
    query.answer()

    assistant = get_user_assistant(user_id)

    # Обработка кнопки переключения на Yandex
    if callback_data == 'provider_yandex':
        try:
            assistant.set_provider('yandex')
            query.edit_message_text(
                "✅ Провайдер переключен на *YandexGPT*\n"
                "История диалога очищена.\n\n"
                "Напиши мне что-нибудь!",
                parse_mode='Markdown',
                reply_markup=create_keyboard()
            )
            logger.info(f"🔄 Пользователь {user_id} переключился на Yandex (кнопка)")
        except Exception as e:
            query.edit_message_text(
                f"❌ Ошибка переключения: {str(e)}",
                reply_markup=create_keyboard()
            )

    # Обработка кнопки переключения на Sber
    elif callback_data == 'provider_sber':
        try:
            assistant.set_provider('sber')
            query.edit_message_text(
                "✅ Провайдер переключен на *GigaChat (SberAI)*\n"
                "История диалога очищена.\n\n"
                "Напиши мне что-нибудь!",
                parse_mode='Markdown',
                reply_markup=create_keyboard()
            )
            logger.info(f"🔄 Пользователь {user_id} переключился на Sber (кнопка)")
        except Exception as e:
            query.edit_message_text(
                f"❌ Ошибка переключения: {str(e)}",
                reply_markup=create_keyboard()
            )

    # Обработка кнопки очистки истории
    elif callback_data == 'clear_history':
        messages_before = assistant.get_history_length()
        assistant.clear_history()
        query.edit_message_text(
            f"🗑 История диалога очищена!\n"
            f"Удалено сообщений: {messages_before}\n\n"
            f"*Текущий провайдер:* {assistant.provider.upper()}\n\n"
            "Можешь начать новый разговор.",
            parse_mode='Markdown',
            reply_markup=create_keyboard()
        )
        logger.info(f"🗑 Пользователь {user_id} очистил историю (кнопка)")

    # Обработка кнопки информации
    elif callback_data == 'info':
        info_message = (
            "ℹ️ *Информация о боте*\n\n"
            f"🤖 *Текущий провайдер:* {assistant.provider.upper()}\n"
            f"💬 *Сообщений в истории:* {assistant.get_history_length()}\n\n"
            "*Поддерживаемые провайдеры:*\n"
            "• YandexGPT (Yandex Cloud)\n"
            "• GigaChat (SberAI)\n\n"
            "*Разработчик:* ZeroCode University"
        )
        query.edit_message_text(
            info_message,
            parse_mode='Markdown',
            reply_markup=create_keyboard()
        )


def error_handler(update: Update, context: CallbackContext):
    """Обработчик ошибок"""
    logger.error(f"⚠️ Update {update} вызвал ошибку: {context.error}")


def main():
    """Основная функция запуска бота"""
    logger.info("🚀 Запуск AI-ассистента...")

    try:
        # Создаем Updater и передаем токен бота
        updater = Updater(token=TELEGRAM_TOKEN, use_context=True)

        # Получаем диспетчер для регистрации обработчиков
        dispatcher = updater.dispatcher

        # Регистрируем обработчики команд
        dispatcher.add_handler(CommandHandler('start', start))
        dispatcher.add_handler(CommandHandler('yandex', yandex_command))
        dispatcher.add_handler(CommandHandler('sber', sber_command))
        dispatcher.add_handler(CommandHandler('clear', clear_command))
        dispatcher.add_handler(CommandHandler('info', info_command))

        # Регистрируем обработчик callback-кнопок
        dispatcher.add_handler(CallbackQueryHandler(button_callback))

        # Регистрируем обработчик текстовых сообщений
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

        # Регистрируем обработчик ошибок
        dispatcher.add_error_handler(error_handler)

        # Запускаем бота
        logger.info("✅ Бот запущен и готов к работе!")
        logger.info("Нажмите Ctrl+C для остановки бота")
        updater.start_polling()

        # Останавливаем бота при нажатии Ctrl+C
        updater.idle()

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        raise
    finally:
        logger.info("🛑 Бот остановлен")


if __name__ == '__main__':
    main()

