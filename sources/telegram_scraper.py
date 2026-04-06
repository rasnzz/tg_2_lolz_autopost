import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time
from datetime import datetime


def scrape_telegram_channel(channel_username):
    """
    Парсить посты из публичного Telegram-канала без использования API
    """
    # Обработать оба формата: @channel_name и channel_name
    if channel_username.startswith('@'):
        channel_name = channel_username[1:]
    else:
        channel_name = channel_username
    
    url = f"https://t.me/s/{channel_name}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Ошибка получения канала {channel_username}: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    posts = []
    
    # Найти все элементы сообщений
    message_elements = soup.find_all('div', class_='tgme_widget_message')
    
    for msg_elem in message_elements[:10]:  # Ограничить последними 10 постами
        try:
            # Извлечь ID поста
            post_link = msg_elem.find('a', class_='tgme_widget_message_date')
            post_id = None
            if post_link and post_link.get('href'):
                post_id = post_link['href'].split('/')[-1]
            
            # Извлечь текст
            text_elem = msg_elem.find('div', class_='tgme_widget_message_text')
            text = ""
            if text_elem:
                # Заменить теги <br> на символы новой строки для сохранения переносов
                for br in text_elem.find_all('br'):
                    br.replace_with('\n')
                text = text_elem.get_text(strip=False)  # Сохранить форматирование
            
            # Извлечь изображения - исключить фото профиля/аватары
            images = []
            photo_links = msg_elem.find_all('a', class_='tgme_widget_message_photo_wrap')
            for link in photo_links:
                style = link.get('style', '')
                # Извлечь URL из стиля background-image
                urls = re.findall(r'url\(["\']?(.*?)["\']?\)', style)
                for img_url in urls:
                    # Пропустить если выглядит как фото профиля или аватар
                    if not is_avatar_url(img_url):
                        images.append(img_url)
                    
            # Также проверить отдельные теги изображений, исключая аватары
            img_tags = msg_elem.find_all('img')
            for img_tag in img_tags:
                if img_tag.get('src'):
                    img_src = img_tag['src']
                    # Исключить изображения аватаров/профилей
                    if not is_avatar_url(img_src):
                        images.append(img_src)
            
            # Извлечь дату
            time_elem = msg_elem.find('time')
            date = None
            if time_elem and time_elem.get('datetime'):
                date = datetime.fromisoformat(time_elem['datetime'].replace('Z', '+00:00'))
            
            if post_id and (text or images):  # Добавлять только посты с содержимым
                posts.append({
                    'id': post_id,
                    'text': text,
                    'images': images,
                    'date': date,
                    'channel': channel_username
                })
        except Exception as e:
            print(f"Ошибка парсинга поста в {channel_username}: {e}")
            continue
    
    return posts


def is_avatar_url(url):
    """
    Проверить, является ли URL изображением аватара/профиля
    """
    url_lower = url.lower()
    avatar_indicators = [
        'avatar', 'userpic', 'profile', 'photo_50', 'photo_100', 
        'photo_200', 'photo_400', 'photo_800', 's=user', 'sz=s',
        'c=avatar', 'image_type=avatar', 'size=avatar'
    ]
    
    # Проверить наличие индикаторов аватара в URL
    for indicator in avatar_indicators:
        if indicator in url_lower:
            return True
    
    # Также проверить общие паттерны аватаров
    avatar_patterns = [
        r'/avatars?/',
        r'/photos?.*small/',
        r'/photos?.*thumb/',
        r'/users?.*/photos?',
        r'/profile_pics?/'
    ]
    
    for pattern in avatar_patterns:
        if re.search(pattern, url_lower):
            return True
    
    return False