import os
import yaml
import time
import hashlib
import requests
from config.config_generator import generate_config
from sources.telegram_scraper import scrape_telegram_channel
from processors.post_processor import filter_post
from poster.lolz_poster import post_to_lolz
from utils.logger import log_info, log_error, setup_logger

setup_logger()

# Set to store post IDs during runtime to avoid duplicates in one run
posted_ids = set()
# Track the time of the last post to enforce delay
last_post_time = 0


def get_forum_list(api_token):
    """
    Fetch the list of forums from lolz.live API
    """
    url = "https://prod-api.lolz.live/forums"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)  # Increased timeout slightly
        
        if response.status_code == 200:
            forums_data = response.json()
            
            # Based on the actual API response structure seen:
            # The response has a 'forums' array at the root level
            forums = []
            
            if isinstance(forums_data, dict) and 'forums' in forums_data:
                forums = forums_data['forums']
                # Limit to first 50 forums to avoid too much data
                forums = forums[:50]
            
            # Ensure it's a list and return if we got data
            if isinstance(forums, list) and len(forums) > 0:
                return forums
            
        else:
            print(f"Forum list API returned status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Forum list API request error: {type(e).__name__}")
    except ValueError:  # JSON decode error
        print("Forum list API: Could not parse response as JSON")
    
    # If API failed or returned no data, return common forum IDs as fallback
    print("Using common forum list (API access may require specific permissions)...")
    common_forums = [
        {"forum_id": 4, "forum_title": "Жизнь форума"},
        {"forum_id": 7, "forum_title": "CyberSport"},
        {"forum_id": 8, "forum_title": "Games"},
        {"forum_id": 9, "forum_title": "Technology"},
        {"forum_id": 13, "forum_title": "Programming"},
        {"forum_id": 19, "forum_title": "Anime"},
        {"forum_id": 21, "forum_title": "Books"},
        {"forum_id": 35, "forum_title": "Humor"},
        {"forum_id": 128, "forum_title": "Graphics"},
        {"forum_id": 130, "forum_title": "Music"},
        {"forum_id": 175, "forum_title": "Movies"},
        {"forum_id": 200, "forum_title": "Science"},
        {"forum_id": 215, "forum_title": "Auto"},
        {"forum_id": 227, "forum_title": "Talks"},
        {"forum_id": 263, "forum_title": "Browsers"},
        {"forum_id": 343, "forum_title": "Windows"},
        {"forum_id": 345, "forum_title": "Linux"},
        {"forum_id": 347, "forum_title": "MacOS"},
        {"forum_id": 372, "forum_title": "Network"},
        {"forum_id": 381, "forum_title": "Hardware"},
        {"forum_id": 518, "forum_title": "Android"},
        {"forum_id": 536, "forum_title": "iOS"},
        {"forum_id": 588, "forum_title": "Cryptocurrency"},
        {"forum_id": 723, "forum_title": "VPN & Proxy"},
        {"forum_id": 753, "forum_title": "Web Development"}
    ]
    
    return common_forums


def display_forum_list(forums):
    """
    Display a formatted list of forums with IDs and titles
    """
    print("\n=== Available Forums ===")
    print(f"{'ID':<8} {'Title':<50}")
    print("-" * 60)
    
    for forum in forums:
        # Handle different possible structures of forum objects
        forum_id = 'N/A'
        title = 'N/A'
        
        if isinstance(forum, dict):
            # Get forum ID
            if 'forum_id' in forum:
                forum_id = forum['forum_id']
            elif 'node_id' in forum:
                forum_id = forum['node_id']
            elif 'id' in forum:
                forum_id = forum['id']
            
            # Get forum title - the actual API uses 'forum_title' not 'title'
            if 'forum_title' in forum:
                title = str(forum['forum_title'])[:47]  # Limit title length
            elif 'title' in forum:
                title = str(forum['title'])[:47]
            elif 'node_title' in forum:
                title = str(forum['node_title'])[:47]
            elif 'name' in forum:
                title = str(forum['name'])[:47]
        
        print(f"{forum_id:<8} {title:<50}")
    
    print("-" * 60)


def main():
    global last_post_time
    
    # Удалить старый конфиг если существует
    if os.path.exists("config.yaml"):
        os.remove("config.yaml")
        print("Удален старый config.yaml")

    print("=== Настройка автопостера из Telegram в Lolz.live ===")
    
    # Сначала получить токен API
    api_token = input("Введите токен API lolz.live: ").strip()
    
    # Сначала получить и отобразить список форумов
    print("\nПолучение списка форумов из API lolz.live...")
    forums = get_forum_list(api_token)
    if forums:
        display_forum_list(forums)
    else:
        print("Не удалось получить список форумов. Переход к ручному вводу.")
    
    # Теперь запросить ID целевых форумов
    target_forums_input = input("\nВведите ID целевых форумов (через запятую, например, 128, 876): ").strip()
    target_forums = [int(fid.strip()) for fid in target_forums_input.split(",") if fid.strip()]
    
    # Теперь запросить Telegram каналы
    telegram_channels_input = input("Введите Telegram каналы (через запятую, например, @channel1, @channel2): ").strip()
    telegram_channels = [ch.strip() for ch in telegram_channels_input.split(",") if ch.strip()]
    
    stop_words_input = input("Введите стоп-слова (через запятую, опционально, нажмите Enter чтобы пропустить): ").strip()
    stop_words = [word.strip() for word in stop_words_input.split(",") if word.strip()] if stop_words_input else []
    
    min_length_input = input("Введите минимальную длину поста (по умолчанию 50): ").strip()
    min_length = int(min_length_input) if min_length_input.isdigit() else 50
    
    max_length_input = input("Введите максимальную длину поста (по умолчанию 2000): ").strip()
    max_length = int(max_length_input) if max_length_input.isdigit() else 2000
    
    delay_input = input("Введите задержку между постами в секундах (минимум 300, по умолчанию 300): ").strip()
    min_delay = int(delay_input) if delay_input.isdigit() else 300
    # Принудительно установить минимальную задержку 300 секунд как требуется
    min_delay = max(min_delay, 300)
    
    title_prefix = input("Введите префикс заголовка (опционально, нажмите Enter чтобы пропустить): ").strip()
    if not title_prefix:
        title_prefix = ""

    # Генерировать файл конфигурации
    config = {
        'api_token': api_token,
        'sources': {
            'telegram_channels': telegram_channels
        },
        'target_forums': target_forums,
        'filters': {
            'stop_words': stop_words,
            'min_length': min_length,
            'max_length': max_length
        },
        'settings': {
            'min_delay': min_delay
        },
        'title_prefix': title_prefix
    }
    
    generate_config(config)
    print("Файл конфигурации успешно создан!")

    # Загрузить конфиг
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Основной цикл публикации
    for channel in config['sources']['telegram_channels']:
        print(f"Обработка канала: {channel}")
        
        # Получить последние посты из канала
        posts = scrape_telegram_channel(channel)
        
        for post in posts:
            # Создать хеш поста для обнаружения дубликатов за это выполнение
            post_hash = hashlib.md5((post['text'] + ''.join(post['images'])).encode()).hexdigest()
            
            # Пропустить если мы уже обработали этот пост за это выполнение
            if post_hash in posted_ids:
                print(f"Пропуск дубликата поста: {post['id']}")
                continue
            
            # Проверить фильтры
            if not filter_post(post, config['filters']):
                print(f"Пост отфильтрован: {post['id']}")
                continue
            
            # Обработать и опубликовать во все целевые форумы
            for forum_id in config['target_forums']:
                print(f"Попытка опубликовать в форум {forum_id}")
                
                # Принудительно обеспечить минимальную задержку между постами
                current_time = time.time()
                time_since_last_post = current_time - last_post_time
                if time_since_last_post < config['settings']['min_delay']:
                    remaining_delay = config['settings']['min_delay'] - time_since_last_post
                    print(f"Ожидание {remaining_delay:.1f} секунд для соблюдения минимальной задержки...")
                    time.sleep(remaining_delay)
                
                # Отправить в lolz
                success = post_to_lolz(
                    api_token=config['api_token'],
                    forum_id=forum_id,
                    title=f"{config['title_prefix']}{post['text'][:70]}...",
                    body=post['text'] + "\n" + "\n".join([f"[img]{img}[/img]" for img in post['images']]),
                    min_delay=config['settings']['min_delay']
                )
                
                if success:
                    posted_ids.add(post_hash)
                    last_post_time = time.time()  # Обновить время последнего поста
                    log_info(f"Успешно опубликовано {post['id']} в форум {forum_id}")
                else:
                    log_error(f"Не удалось опубликовать {post['id']} в форум {forum_id}")


if __name__ == "__main__":
    main()