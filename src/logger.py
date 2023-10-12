import logging

class NoFapLogger(object):
    def __new__(cls):
        if not hasattr(cls, 'logger'):
            cls.logger = logging.getLogger("no_fap_logger")
            cls.logger.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

            file_handler = logging.FileHandler('no_fap_bot.log')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)

            cls.logger.addHandler(file_handler)
            def infoMessage(message):
                cls.logger.info(f"{message.chat.username}({message.chat.id}): "
                                + message.text if message.text else message.content_type)
            setattr(cls.logger, 'infoMessage', infoMessage)
        return cls.logger

noFapLogger = NoFapLogger()
