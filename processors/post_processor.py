import hashlib
import re


def filter_post(post, filters):
    """
    Применить фильтры чтобы определить должен ли пост быть опубликован
    """
    # Удалить имена пользователей (@упоминания) и хэштеги которые выглядят как имена пользователей из текста
    cleaned_text = remove_usernames_and_hashtags(post['text'])
    post['text'] = cleaned_text  # Обновить текст поста после очистки
    
    text = cleaned_text.lower()
    
    # Проверить стоп-слова
    for stop_word in filters.get('stop_words', []):
        if stop_word.lower() in text:
            return False
    
    # Проверить длину
    text_length = len(cleaned_text)
    if text_length < filters.get('min_length', 0):
        return False
    
    if text_length > filters.get('max_length', float('inf')):
        return False
    
    return True


def remove_usernames_and_hashtags(text):
    """
    Удалить имена пользователей (@упоминания) и некоторые хэштеги (например, @что-то) из текста
    """
    # Удалить @упоминания и @хэштеги которые выглядят как имена пользователей
    # Это соответствует @ за которым следуют словесные символы (буквы, цифры, подчеркивания, дефисы)
    username_pattern = r'@\w+'
    cleaned_text = re.sub(username_pattern, '', text)
    
    # Удалить лишние пробелы оставшиеся после удаления имен пользователей
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text


def generate_post_hash(post):
    """
    Сгенерировать хеш для поста чтобы обнаружить дубликаты
    """
    content = post['text'] + ''.join(post['images'])
    return hashlib.md5(content.encode()).hexdigest()