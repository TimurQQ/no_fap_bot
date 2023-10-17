import aiogram
import logging
from src.constants import *
import types

class NoFapLogger(object):
    _commandLogger = None
    _cronLogger = None

    _instance = None

    @staticmethod
    def _turnOnConsoleLogging(logger):
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)

    @staticmethod
    def _turnOffConsoleLogging(logger):
        # I have no idea how to turn off logging into console.
        # Approach with remove StreamHandler from logger doesn't working
        pass

    def set_console_logging(self, consoleLogging):
        if not consoleLogging:
            self._turnOnConsoleLogging(self._commandLogger)
            self._turnOnConsoleLogging(self._cronLogger)
        else:
            self._turnOffConsoleLogging(self._commandLogger)
            self._turnOffConsoleLogging(self._cronLogger)

    def __new__(cls):
        if cls._instance is None:
            cls._commandLogger = logging.getLogger(LOGGER_NAME)
            cls._cronLogger = logging.getLogger(SCHEDULE_LOGGER_NAME)

            cls._commandLogger.setLevel(logging.INFO)
            cls._cronLogger.setLevel(logging.INFO)

            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

            file_handler = logging.FileHandler("no_fap_bot.log")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)

            cls._commandLogger.addHandler(file_handler)
            cls._cronLogger.addHandler(file_handler)

            cls._instance = super(NoFapLogger, cls).__new__(cls)

        return cls._instance

    def info(self, text: str):
        self._commandLogger.info(text)

    def info_message(self, message: aiogram.types.Message):
        self._commandLogger.info(f"{message.chat.username}({message.chat.id}): "
                                 + message.text if message.text else message.content_type)
