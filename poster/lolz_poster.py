import requests
import time
import random
from utils.logger import log_info, log_error


def post_to_lolz(api_token, forum_id, title, body, min_delay=200):
    """
    Публиковать на форум lolz.live используя API
    """
    url = "https://prod-api.lolz.live/threads"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Подготовить данные
    payload = {
        "forum_id": forum_id,
        "title": title[:100],  # Ограничить длину заголовка
        "post_body": body[:5000]  # Ограничить длину тела
    }
    
    # Попытаться опубликовать с логикой повторных попыток
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                # Успешно
                thread_id = response.json().get('thread', {}).get('thread_id')
                log_info(f"Успешно опубликовано на форум {forum_id}, ID темы: {thread_id}")
                
                # Ждать минимальную задержку плюс случайное значение
                jitter = random.uniform(0, 30)
                time.sleep(min_delay + jitter)
                
                return True
                
            elif response.status_code == 400:
                log_error(f"Неверный запрос при публикации на форум {forum_id}: {response.text}")
                return False  # Не повторять неверные запросы
                
            elif response.status_code == 401:
                log_error(f"Неавторизованный доступ к форуму {forum_id}. Проверьте ваш токен API.")
                return False  # Не повторять неавторизованные запросы
                
            elif response.status_code == 403:
                log_error(f"Запрещено: Нет разрешения публиковать на форуме {forum_id}")
                return False  # Не повторять запрещенные запросы
                
            elif response.status_code == 404:
                log_error(f"Форум {forum_id} не найден")
                return False  # Не повторять если форум не существует
                
            elif response.status_code == 429:
                # Ограничение скорости - ждать и повторить
                log_error(f"Ограничение скорости при публикации на форуме {forum_id}, ожидание...")
                time.sleep(2)
                continue  # Повторить
                
            elif response.status_code >= 500:
                # Ошибка сервера - ждать и повторить
                log_error(f"Ошибка сервера при публикации на форуме {forum_id}, ожидание...")
                time.sleep(5)
                continue  # Повторить
                
            else:
                log_error(f"Неизвестная ошибка при публикации на форуме {forum_id}: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            log_error(f"Исключение запроса при публикации на форуме {forum_id}: {e}")
            if attempt < 2:  # Не ждать после последней попытки
                time.sleep(5)
            continue
    
    log_error(f"Не удалось опубликовать на форуме {forum_id} после 3 попыток")
    return False


def check_forum_permission(api_token, forum_id):
    """
    Проверить есть ли у аккаунта разрешение создавать темы на форуме
    """
    url = f"https://prod-api.lolz.live/forums/{forum_id}"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            forum_data = response.json()
            permissions = forum_data.get('forum', {}).get('permissions', {})
            return permissions.get('create_thread', False)
        else:
            log_error(f"Ошибка проверки разрешений форума для {forum_id}: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        log_error(f"Исключение запроса при проверке разрешений форума: {e}")
        return False