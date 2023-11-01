import os
import re
import json
import aiogram
import asyncio
import logging
import shutil
from src.utils.json_encoder import EnhancedJSONEncoder
from logging.handlers import TimedRotatingFileHandler
from datetime import time, datetime
from src.constants import (
    LOG_FILENAME,
    LOGS_FOLDER,
    NO_FAP_LOGGER_NAME,
    SCHEDULER_LOGGER_NAME,
    BACKUP_FOLDER,
)
from singleton_decorator import singleton


class NoFapTimedRotatingFileHandler(TimedRotatingFileHandler):
    def setLogsSender(self, logsSender):
        self._logsSender = logsSender

    def doRollover(self):
        super().doRollover()

        if self._logsSender:
            loop = asyncio.get_running_loop()

            target = sorted(os.listdir(LOGS_FOLDER))[-1]

            task = loop.create_task(self._logsSender(os.path.join(LOGS_FOLDER, target)))
            task.add_done_callback(
                lambda _: shutil.move(
                    os.path.join(LOGS_FOLDER, target),
                    os.path.join(
                        BACKUP_FOLDER, f"{target}-{datetime.now().timestamp()}"
                    ),
                )
            )


@singleton
class NoFapLogger(object):
    _commandLogger = None
    _cronLogger = None

    @staticmethod
    def _turnOnConsoleLogging(logger):
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)

    @staticmethod
    def _turnOffConsoleLogging(logger):
        logger.propagate = False

    def set_console_logging(self, consoleLogging):
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

    def setLoggerSender(self, loggerSender):
        self._file_handler.setLogsSender(loggerSender)

    def info(self, text: str):
        self._commandLogger.info(text)

    def error(self, text: str):
        self._commandLogger.error(text)

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
