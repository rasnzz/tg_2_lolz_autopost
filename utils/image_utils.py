def extract_direct_image_urls(html_content):
    """
    Извлечь прямые URL-адреса изображений из HTML-контента
    """
    import re
    
    # Шаблон для соответствия URL-адресов изображений в различных форматах
    img_pattern = r'https?://[^\s\'"<>]+?\.(?:jpg|jpeg|png|gif|webp|bmp|tiff|svg)[^\s\'"<>]*'
    urls = re.findall(img_pattern, html_content, re.IGNORECASE)
    
    return urls


def validate_image_url(url):
    """
    Проверить является ли URL действительным URL-адресом изображения
    """
    import re
    
    # Простая проверка для расширений файлов изображений
    img_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff']
    return any(ext in url.lower() for ext in img_extensions)


def convert_to_bbcode_images(image_urls):
    """
    Конвертировать URL-адреса изображений в формат bbcode
    """
    bbcode_images = []
    for url in image_urls:
        bbcode_images.append(f"[img]{url}[/img]")
    
    return bbcode_images