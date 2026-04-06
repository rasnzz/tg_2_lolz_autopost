import yaml


def generate_config(config_data):
    """
    Генерировать config.yaml из предоставленных данных конфигурации
    """
    with open('config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)