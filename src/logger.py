import asyncio
import json
import logging
import os
import re
import shutil
from datetime import datetime, time
from logging.handlers import TimedRotatingFileHandler
from typing import Callable, Optional, Tuple

import aiogram
from singleton_decorator import singleton

from src.constants import (
    BACKUP_FOLDER,
    LOG_FILENAME,
    LOGS_FOLDER,
    NO_FAP_LOGGER_NAME,
    SCHEDULER_LOGGER_NAME,
)
from src.utils.json_encoder import EnhancedJSONEncoder


class NoFapTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logsSender = None

    def setLogsSender(self, logsSender: Callable):
        self._logsSender = logsSender

    async def _send_log_file_to_admins(
        self, target_path: str, target_name: str, logger: logging.Logger
    ):
        """Асинхронная отправка лог файла админам и перемещение в backup"""
        try:
            logger.info(f"📤 Начинается отправка лога {target_name} админам")
            await self._logsSender(target_path)
            logger.info(f"✅ Лог {target_name} успешно отправлен админам")

            # После успешной отправки перемещаем файл в backup
            if not os.path.exists(BACKUP_FOLDER):
                os.makedirs(BACKUP_FOLDER)
                logger.info(f"📁 Создана папка backup: {BACKUP_FOLDER}")

            backup_path = os.path.join(
                BACKUP_FOLDER, f"{target_name}-{datetime.now().timestamp()}"
            )
            shutil.move(target_path, backup_path)
            logger.info(
                f"📤 Лог {target_name} отправлен админам и перемещен в backup: {backup_path}"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке лога {target_name}: {e}")
            logger.error(f"❌ Детали ошибки: {type(e).__name__}: {str(e)}")

    def _find_latest_log_file(
        self, logger: logging.Logger
    ) -> Tuple[Optional[str], Optional[str]]:
        """Находит последний файл лога для отправки"""
        target = sorted(os.listdir(LOGS_FOLDER))[-1]
        target_path = os.path.join(LOGS_FOLDER, target)
        logger.info(f"📄 Найден файл лога для отправки: {target}")

        if not os.path.exists(target_path):
            logger.error(f"❌ Файл лога не существует: {target_path}")
            return None, None

        return target, target_path

    def _schedule_log_sending(
        self, target_path: str, target_name: str, logger: logging.Logger
    ):
        """Планирует отправку лога с учетом текущего event loop"""
        try:
            # Пытаемся использовать существующий loop
            loop = asyncio.get_running_loop()
            logger.info("⚙️ Используется существующий event loop")
            self._create_async_task(loop, target_path, target_name, logger)
        except RuntimeError:
            # Создаем новый loop для синхронного выполнения
            logger.info("⚙️ Нет активного loop, создается новый для выполнения")
            self._run_in_new_loop(target_path, target_name, logger)

    def _create_async_task(
        self,
        loop: asyncio.AbstractEventLoop,
        target_path: str,
        target_name: str,
        logger: logging.Logger,
    ):
        """Создает асинхронную задачу в существующем loop"""
        task = loop.create_task(
            self._send_log_file_to_admins(target_path, target_name, logger)
        )
        task.add_done_callback(
            lambda t: (
                logger.info("✅ Task отправки логов завершен")
                if not t.exception()
                else logger.error(
                    f"❌ Task отправки логов завершен с ошибкой: {t.exception()}"
                )
            )
        )

    def _run_in_new_loop(
        self, target_path: str, target_name: str, logger: logging.Logger
    ):
        """Выполняет отправку в новом event loop"""
        new_loop = asyncio.new_event_loop()
        try:
            new_loop.run_until_complete(
                self._send_log_file_to_admins(target_path, target_name, logger)
            )
        finally:
            new_loop.close()

    def doRollover(self):
        super().doRollover()

        logger = logging.getLogger(NO_FAP_LOGGER_NAME)
        logger.info("🔄 Начинается процесс ротации логов")

        # Early return если logsSender не установлен
        if not self._logsSender:
            logger.warning(
                "⚠️ logsSender не установлен! Логи не будут отправлены админам"
            )
            return

        logger.info("📤 logsSender найден, начинаем отправку логов")

        # Находим файл лога
        target_name, target_path = self._find_latest_log_file(logger)
        if not target_path:
            return

        # Планируем отправку
        self._schedule_log_sending(target_path, target_name, logger)


@singleton
class NoFapLogger(object):
    _commandLogger = None
    _cronLogger = None

    @staticmethod
    def _turnOnConsoleLogging(logger: logging.Logger):
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)

    @staticmethod
    def _turnOffConsoleLogging(logger: logging.Logger):
        logger.propagate = False

    def set_console_logging(self, consoleLogging: bool):
        if consoleLogging:
            self._turnOnConsoleLogging(self._commandLogger)
            self._turnOnConsoleLogging(self._cronLogger)
        else:
            self._turnOffConsoleLogging(self._commandLogger)
            self._turnOffConsoleLogging(self._cronLogger)

    def __init__(self):
        self._commandLogger = logging.getLogger(NO_FAP_LOGGER_NAME)
        self._cronLogger = logging.getLogger(SCHEDULER_LOGGER_NAME)

        self._commandLogger.setLevel(logging.INFO)
        self._cronLogger.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

        self._file_handler = NoFapTimedRotatingFileHandler(
            filename=os.path.join(LOGS_FOLDER, LOG_FILENAME),
            when="midnight",
            atTime=time(hour=22, minute=00),
        )
        self._file_handler.setLevel(logging.INFO)
        self._file_handler.setFormatter(formatter)

        self._commandLogger.addHandler(self._file_handler)
        self._cronLogger.addHandler(self._file_handler)

    def setLoggerSender(self, loggerSender: Callable):
        self._file_handler.setLogsSender(loggerSender)
        self._commandLogger.info(
            f"✅ logsSender установлен: {loggerSender.__name__ if hasattr(loggerSender, '__name__') else 'функция без имени'}"
        )

    def info(self, text: str):
        self._commandLogger.info(text)

    def error(self, text: str):
        self._commandLogger.error(text)

    def warning(self, text: str):
        self._commandLogger.warning(text)

    def info_message(self, message: aiogram.types.Message):
        chat = message.chat
        text = message.text
        messageText = text if f'"{text}"' else message.content_type
        self.info(f'User {chat.username} ({chat.id}) send a message: "{messageText}"')

    def logDatabase(self, data):
        data_log = re.sub(
            r'"collectedMemes": \[[^]]*\],\s+',
            "",
            json.dumps(data, cls=EnhancedJSONEncoder, indent=4),
        )
        self.info(f"{data_log}")
