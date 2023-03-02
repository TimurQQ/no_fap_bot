import logging
from aiogram import Bot, Dispatcher
from config.config import BOT_TOKEN
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from src.filters.admin import IsAdminFilter
from src.middlewares.black_list import BlackListMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.filters_factory.bind(IsAdminFilter)
dp.middleware.setup(BlackListMiddleware())
