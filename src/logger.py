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
        logger.propagate = False

    def set_console_logging(self, consoleLogging):
        if consoleLogging:
            self._turnOnConsoleLogging(self._commandLogger)
            self._turnOnConsoleLogging(self._cronLogger)
        else:
            self._turnOffConsoleLogging(self._commandLogger)
            self._turnOffConsoleLogging(self._cronLogger)

    def _createLoggers(self):
        self._commandLogger = logging.getLogger(NO_FAP_LOGGER_NAME)
        self._cronLogger = logging.getLogger(SCHEDULER_LOGGER_NAME)

        self._commandLogger.setLevel(logging.INFO)
        self._cronLogger.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

        file_handler = logging.FileHandler(LOG_FILENAME)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        self._commandLogger.addHandler(file_handler)
        self._cronLogger.addHandler(file_handler)

    def __new__(cls):
        if cls._instance is None:
            cls._createLoggers(cls)

            cls._instance = super(NoFapLogger, cls).__new__(cls)

        return cls._instance

    def info(self, text: str):
        self._commandLogger.info(text)

    def info_message(self, message: aiogram.types.Message):
        chat = message.chat
        text = message.text
        self._commandLogger.info(f"User {chat.username} ({chat.id}) send a message: "
                                 + text if text else message.content_type)

    @staticmethod
    def _removeHandlers(logger):
        logger.handlers.clear()

    @staticmethod
    def _addHandlers(logger, handlers):
        for handler in handlers:
            logger.addHandler(handler)

    def turnOffLogging(self):
        self._removeHandlers(self._commandLogger)
        self._removeHandlers(self._cronLogger)

    def turnOnLogging(self):
        self._createLoggers()
