import logging
from datetime import datetime
import os


def setup_logger():
    """
    Настроить логгер с файловым и консольным обработчиками
    """
    # Создать директорию logs если она не существует
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Создать логгер
    logger = logging.getLogger('autoposter')
    logger.setLevel(logging.INFO)
    
    # Создать файловый обработчик с ежедневной ротацией
    log_filename = f"logs/poster_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Создать консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Создать форматтер
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Добавить обработчики к логгеру
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


def log_info(message):
    """
    Логировать информационное сообщение
    """
    logger = logging.getLogger('autoposter')
    logger.info(message)


def log_error(message):
    """
    Логировать сообщение об ошибке
    """
    logger = logging.getLogger('autoposter')
    logger.error(message)


def log_warning(message):
    """
    Логировать предупреждение
    """
    logger = logging.getLogger('autoposter')
    logger.warning(message)