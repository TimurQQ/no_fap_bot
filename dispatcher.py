import logging
from aiogram import Bot, Dispatcher
from aiogram.bot.api import TelegramAPIServer
from config.config import BOT_TOKEN, USE_LOCAL_SERVER, LOCAL_SERVER_URL
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from src.filters.admin import IsAdminFilter
from src.middlewares.logging import LoggingMiddleware
from src.middlewares.black_list import BlackListMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)

# Создаем бота в зависимости от настроек
if USE_LOCAL_SERVER:
    print(f"🔧 Using local Telegram API server: {LOCAL_SERVER_URL}")
    local_server = TelegramAPIServer.from_base(LOCAL_SERVER_URL)
    bot = Bot(token=BOT_TOKEN, server=local_server)
else:
    print("🌐 Using official Telegram API")
    bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.filters_factory.bind(IsAdminFilter)
dp.middleware.setup(LoggingMiddleware())
dp.middleware.setup(BlackListMiddleware())
