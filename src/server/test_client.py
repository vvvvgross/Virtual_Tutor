import requests
import json

# Загрузка конфигурации
def load_config():
    import yaml
    import os
    import pathlib

    conf_path = os.path.join(pathlib.Path(__file__).parent.parent.absolute(), "config.yaml")
    with open(conf_path, 'r') as conf_file:
        config = yaml.load(conf_file, Loader=yaml.FullLoader)
    return config

# Загрузка конфигурации
config = load_config()

# URL и заголовки для Deepseek API
url = config["auth"]["url"]  # URL из конфигурации
headers = {
    'Authorization': f"Bearer {config['auth']['token']}",  # Токен из конфигурации
}

# Тело запроса
body = {
    'model': 'deepseek-chat',  # Используем модель Deepseek
    'messages': [
        {
            'role': 'system',
            'content': 'You are a helpful assistant.'
        },
        {
            'role': 'user',
            'content': 'Hello!'
        }
    ]
}

# Отправка запроса
response = requests.post(url=url, headers=headers, json=body)

# Вывод ответа
if response.ok:
    print("Ответ от Deepseek API:")
    print(response.json())
else:
    print("Ошибка при запросе к Deepseek API:")
    print(response.status_code, response.text)