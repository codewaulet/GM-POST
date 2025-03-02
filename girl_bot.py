import asyncio
import logging
import random
from telethon import TelegramClient, events
from g4f.client import AsyncClient
from colorama import Fore, Style, init

# Инициализация colorama
init(autoreset=True)

# Настройка цветного логирования
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        log_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, Fore.WHITE)}{log_message}{Style.RESET_ALL}"

# Логирование
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# 🔹 Конфигурация Telegram
TELEGRAM_API_ID = ""
TELEGRAM_API_HASH = ""
SESSION_NAME = "my_bot_session"

# 🔹 Отслеживаемые каналы и чаты
WATCHED_CHANNELS = [
    "klientvsprav", "why4ch", "zicelaqo", "notforfans", "c_bulgo", "Dota2",
    "cryptoniumb", "laboratorynft", "fackblock", "defigencapital", "cryptodaily",
    "keep_calm_official", "cryptobrelgin", "sybilders", "capycryptos", "tradelabteam"
]
WATCHED_CHATS = [
    -1001802256801, "FlappyBirdFlock", "tonnewbie22", -1001795804616, -1002026410789,
    "ARUTAcademy_chat", -1002086260488, "big_balls_birds_ruchat", "TheKaidzenWayChat",
    "klientyt", "fourchat2", "notfanschat", -1002375046256, -1001588500051,
    "fackblockchat", "defigencapitalchat", "capycryptochat", "tradelabchat"
]

# 🔹 Инициализация клиентов Telegram и G4F
client = TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)
ai_client = AsyncClient()

# Список шаблонных фраз при ошибках
ERROR_PHRASES = [
    "хех ну ок", "да ладно", "спок девочки", "ну такое", "пох чил", "бери выше",
    "ща гляну", "ой ну норм", "тихо всё гуд", "хз как-то так", "пфф живем",
    "не парься", "вот прикол", "легкий движ", "как выйдет"
]

# Эмодзи для случайных реакций
REACTION_EMOJIS = ["😎", "✌️", "💕", "🚀", "🌙", "💸", "👾", "🍒"]

# Глобальные переменные для cooldown
last_chat_response = {chat: 0 for chat in WATCHED_CHATS}  # Отдельный cooldown для каждого чата
last_post_time = 0  # Для автопостинга

# Проверка доступности чатов с задержкой
async def validate_chats(chats):
    valid_chats = []
    for chat in chats:
        await asyncio.sleep(0.5)  # Задержка для избежания лимитов
        try:
            entity = await client.get_entity(chat)
            valid_chats.append(chat)
            logger.info(f"Чат {chat} доступен")
        except ValueError as e:
            logger.error(f"Чат {chat} недоступен: {e}")
        except Exception as e:
            logger.error(f"Ошибка проверки чата {chat}: {e}")
    return valid_chats

# 🧠 Генерация комментария
async def generate_comment(post_text):
    prompt = f"""
    ты милая криптанша 20-летняя девчонка на полном чиле всегда в расслабоне  
    любишь крипту тусуешься в чатах как своя без лишнего шума и понтов  
    пишешь мало с маленькой буквы без знаков препинания как реальная девка с улицы  
    всегда добрая слегка подбадриваешь новичков заводишь корешей но не лезешь с советами если не просят  
    общаешься как живая подруга никаких длинных текстов только короткие фразы или одно слово  
    пост {post_text}  
    вали коммент 1 короткая фраза или слово с крипто-вайбом и легким добром  
    звучит как будто тебе немного пох но ты в теме и хочешь помочь  
    никаких запятых тире точек никаких знаков препинания чтобы не спалиться
    """
    try:
        response = await ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            web_search=False
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка генерации коммента: {e}")
        return random.choice(ERROR_PHRASES)

# 🧠 Генерация ответа на комментарий
async def generate_reply(comment_text, post_text):
    prompt = f"""
    ты милая криптанша 20-летняя девчонка тусуешься в комментах на максимальном чиле  
    пост {post_text}  
    чел написал {comment_text}  
    дай ответ 1 короткая фраза или слово иногда 2 фразы но супер кратко  
    будь добрая поддерживай или шути как реальная подруга с улицы без напряга  
    если вопрос про крипту отвечай чуть живее но все еще коротко и на расслабоне  
    пиши с маленькой буквы без знаков препинания как будто ленишься ставить точки  
    звучит как живой чел никаких намеков на бота только уличный вайб и доброта
    """
    try:
        response = await ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            web_search=False
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка генерации ответа: {e}")
        return random.choice(ERROR_PHRASES)

# 📬 Публикация в закрытый чат/канал с шансом эмодзи
async def post_to_closed_chat(chat_id, message):
    if random.random() < 0.2:  # 20% шанс добавить эмодзи
        message += " " + random.choice(REACTION_EMOJIS)
    try:
        await client.send_message(chat_id, message)
        logger.info(f"Сообщение отправлено в {chat_id}: {message}")
    except Exception as e:
        logger.error(f"Ошибка отправки в закрытый чат {chat_id}: {e}")

# 🎯 Мониторинг новых постов в каналах с вариативностью
@client.on(events.NewMessage(chats=WATCHED_CHANNELS))
async def new_post_handler(event):
    logger.info('🎯 Обнаружен новый пост')
    post_text = event.message.text
    if post_text and random.random() < 0.75:  # 75% шанс комментировать
        comment = await generate_comment(post_text)
        delay = random.randint(20, 240)  # Задержка 20 сек - 4 мин
        await asyncio.sleep(delay)
        try:
            if random.random() < 0.1:  # 10% шанс просто эмодзи
                comment = random.choice(REACTION_EMOJIS)
            await client.send_message(
                entity=event.message.peer_id,
                message=comment,
                comment_to=event.message.id
            )
            logger.info(f"📝 Бот прокомментировал пост: {comment}")
        except Exception as e:
            logger.error(f"Ошибка отправки коммента: {e}")

# 🔄 Ответы на комментарии бота с вариативностью
@client.on(events.NewMessage(incoming=True))
async def reply_handler(event):
    if event.is_reply:
        original_message = await event.get_reply_message()
        bot_id = (await client.get_me()).id
        if original_message and original_message.sender_id == bot_id and random.random() < 0.5:  # 50% шанс ответа
            reply_text = await generate_reply(event.message.text, original_message.text)
            delay = random.randint(5, 90)  # Задержка 5 сек - 1.5 мин
            await asyncio.sleep(delay)
            try:
                if random.random() < 0.15:  # 15% шанс эмодзи вместо текста
                    reply_text = random.choice(REACTION_EMOJIS)
                await event.reply(reply_text)
                logger.info(f"🔄 Бот ответил: {reply_text}")
            except Exception as e:
                logger.error(f"Ошибка ответа в комментах: {e}")

# 💬 Реагирование в чатах с индивидуальным cooldown
@client.on(events.NewMessage(chats=WATCHED_CHATS))
async def chat_handler(event):
    chat_id = event.chat_id
    current_time = asyncio.get_event_loop().time()
    if (current_time - last_chat_response.get(chat_id, 0) >= 600) and random.random() < 0.1:  # Cooldown 10 мин, 10% шанс
        reply_text = await generate_reply(event.message.text, "Беседа в чате")
        delay = random.randint(10, 120)  # Задержка 10 сек - 2 мин
        await asyncio.sleep(delay)
        try:
            if random.random() < 0.2:  # 20% шанс эмодзи
                reply_text = random.choice(REACTION_EMOJIS)
            await event.reply(reply_text)
            last_chat_response[chat_id] = current_time
            logger.info(f"💬 Бот влез в чат {chat_id}: {reply_text}")
        except Exception as e:
            logger.error(f"Ошибка в чате {chat_id}: {e}")

# 🚀 Автопостинг в случайный закрытый чат с глобальным cooldown
async def auto_post_task():
    global last_post_time
    while True:
        await asyncio.sleep(random.randint(1800, 7200))  # 1-4 часа
        current_time = asyncio.get_event_loop().time()
        if current_time - last_post_time >= 3600:  # Минимум 1 час между постами
            message = await generate_comment("крипта врывается девки")
            chat = random.choice(WATCHED_CHATS)
            await post_to_closed_chat(chat, message)
            last_post_time = current_time

# 🔧 Запуск бота с обработкой исключений
async def main():
    try:
        await client.start()
        global WATCHED_CHATS
        WATCHED_CHATS = await validate_chats(WATCHED_CHATS)
        if not WATCHED_CHATS:
            logger.warning("Нет доступных чатов в WATCHED_CHATS автопостинг отключен")
        else:
            logger.info(f"Доступные чаты: {len(WATCHED_CHATS)}")
        logger.info("🔥 Бот запущен и чиллит!")
        asyncio.create_task(auto_post_task())
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}")
    finally:
        await ai_client.session.close()
        logger.info("Сессия AI клиента закрыта")

if __name__ == "__main__":
    asyncio.run(main())