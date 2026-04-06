import re


def clean_text(html_text):
    """
    Очистить HTML-текст из Telegram, заменив <br> на \n и удалив лишнее форматирование
    """
    # Заменить теги <br> на символы новой строки
    cleaned = re.sub(r'<br\s*/?>', '\n', html_text)
    
    # Удалить другие HTML-теги но оставить содержимое
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    
    # Нормализовать пробелы
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)  # Заменить множественные символы новой строки на двойной символ
    cleaned = cleaned.strip()
    
    return cleaned


def extract_title(text, max_len=100, prefix=""):
    """
    Извлечь заголовок из текста, ограничив длину и добавив префикс если указан
    """
    # Получить первые max_len символов
    title = text[:max_len].strip()
    
    # Попытаться разрезать на последнем пробеле чтобы избежать разрезания слов
    if len(text) > max_len:
        last_space = title.rfind(' ')
        if last_space > 0:
            title = title[:last_space]
    
    # Добавить префикс если указан
    if prefix:
        title = f"{prefix}{title}"
    
    return title