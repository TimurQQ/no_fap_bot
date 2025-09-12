import json
import os
from datetime import time


class LogRotationConfig:
    """Конфигурация времени ротации логов"""

    def __init__(self, config_file: str = None):
        """
        Args:
            config_file: Путь к файлу конфигурации. По умолчанию logs/rotation_config.json
        """
        self.config_file = config_file or os.path.join("logs", "rotation_config.json")

    def get_rotation_time(self):
        """Возвращает (час, минута) или (22, 0) по умолчанию"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    hour = config.get("hour", 22)
                    minute = config.get("minute", 0)
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return hour, minute
        except:
            pass
        return 22, 0

    def set_rotation_time(self, hour, minute):
        """Сохраняет время ротации"""
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return False

        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump({"hour": hour, "minute": minute}, f)
            return True
        except:
            return False

    def get_time_object(self):
        """Возвращает объект time для TimedRotatingFileHandler"""
        hour, minute = self.get_rotation_time()
        return time(hour=hour, minute=minute)

    def format_time(self):
        """Возвращает время в формате HH:MM"""
        hour, minute = self.get_rotation_time()
        return f"{hour:02d}:{minute:02d}"
