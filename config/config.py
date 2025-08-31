from os import getenv
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN", None)
USE_LOCAL_SERVER = getenv("USE_LOCAL_SERVER", "false").lower() == "true"
LOCAL_SERVER_URL = getenv("LOCAL_SERVER_URL", "http://localhost:8081")

# S3 Configuration for database backups
S3_ENABLED = getenv("S3_ENABLED", "false").lower() == "true"
S3_BUCKET_NAME = getenv("S3_BUCKET_NAME", "")
S3_ACCESS_KEY = getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = getenv("S3_SECRET_KEY", "")
S3_REGION = getenv("S3_REGION", "us-east-1")
S3_ENDPOINT = getenv("S3_ENDPOINT", "")
