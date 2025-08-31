from os import getenv
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN", None)
USE_LOCAL_SERVER = getenv("USE_LOCAL_SERVER", "false").lower() == "true"
LOCAL_SERVER_URL = getenv("LOCAL_SERVER_URL", "http://localhost:8081")
