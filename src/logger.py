import logging
from logging import StreamHandler

class NoFapLogger(object):
    _comandLogger = None
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
            self._turnOnConsoleLogging(self._comandLogger)
            self._turnOnConsoleLogging(self._cronLogger)
        else:
            self._turnOffConsoleLogging(self._comandLogger)
            self._turnOffConsoleLogging(self._cronLogger)

    def __new__(cls):
        if cls._instance is None:
            cls._comandLogger = logging.getLogger("no_fap_logger")
            cls._cronLogger = logging.getLogger('apscheduler.executors.default')

            cls._comandLogger.setLevel(logging.INFO)
            cls._cronLogger.setLevel(logging.INFO)

            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

            file_handler = logging.FileHandler("no_fap_bot.log")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)

            cls._comandLogger.addHandler(file_handler)
            cls._cronLogger.addHandler(file_handler)

            cls._instance = super(NoFapLogger, cls).__new__(cls)

        return cls._instance

    def info(self, text):
        self._comandLogger.info(text)

    def info_message(self, message):
        self._comandLogger.info(f"{message.chat.username}({message.chat.id}): "
                                + message.text if message.text else message.content_type)

noFapLogger = NoFapLogger()
