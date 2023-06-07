import logging
from src.telegram_handler import telegram_send_message_to

try:
    from cStringIO import StringIO  # Python 2
except ImportError:
    from io import StringIO


def on_log(record):
    telegram_send_message_to(record.getMessage())
    return True


def setup_logger():
    format_ = '%(asctime)-15s %(levelname)-6s %(message)s'
    date_format = '%b %d %H:%M:%S'
    formatter = logging.Formatter(fmt=format_, datefmt=date_format)

    # General logging
    logger = logging.getLogger("main")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Used only for the telegram Bot
    log_stream = StringIO()
    logger_2 = logging.getLogger("telegram")
    handler_2 = logging.StreamHandler(log_stream)
    handler_2.setFormatter(formatter)
    logger_2.setLevel(logging.INFO)
    logger_2.addHandler(handler_2)
    logging.root.addFilter(on_log)
    return logger

