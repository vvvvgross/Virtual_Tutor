import numpy as np
import re
import requests
import json
import helper as hlp
import time

class Interface:
    """Класс для взаимодействия с Deepseek API"""
    
    def __init__(self):
        """Инициализация с загрузкой конфигурации"""
        config = hlp.load_config()
        self.token = config["auth"]["token"]  # API-ключ
        self.base_url = config["auth"]["url"].rstrip('/')  # Базовый URL API
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.timeout = 30  # Таймаут запроса в секундах
        self.max_retries = 3  # Максимальное количество попыток

    def _make_api_request(self, endpoint, body):
        """
        Внутренний метод для отправки запросов с повторными попытками
        
        Args:
            endpoint (str): Конечная точка API (например "/chat/completions")
            body (dict): Тело запроса
            
        Returns:
            dict: Ответ API или None при ошибке
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url=url,
                    headers=self.headers,
                    json=body,
                    timeout=self.timeout
                )
                response.raise_for_status()  # Проверка на ошибки HTTP
                return response.json()
            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    raise  # Если последняя попытка - пробрасываем исключение
                time.sleep(1)  # Задержка между попытками
            except requests.exceptions.RequestException:
                return None
        return None

    def clear_intentions(self, reply):
        """
        Извлекает числа из текстового ответа API
        
        Args:
            reply (str): Текст ответа от API (например "0.2, 0.5, 0.1")
            
        Returns:
            list: Список чисел [0.2, 0.5, 0.1]
        """
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", reply)
        return [float(num) if '.' in num else int(num) for num in numbers]

    def get_composition(self, intents_dict, phrase):
        """
        Анализирует интенции во фразе студента
        
        Args:
            intents_dict (dict): Словарь интенций (из helper.py)
            phrase (str): Фраза для анализа
            
        Returns:
            list: Вероятности интенций или None при ошибке
        """
        cat_str = ', '.join(intents_dict.values())
        num = len(intents_dict.values())
        
        # Промпт для анализа интенций
        prompt = f"""
            Ты механизм по определению интенций в речи человека...
            (полный текст промпта)
            {cat_str}
            "{phrase}"
        """
        
        body = {
            'model': 'deepseek-chat',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.1  # Низкая температура для детерминированных ответов
        }

        result = self._make_api_request("/chat/completions", body)
        if result:
            return self.clear_intentions(result["choices"][0]["message"]["content"])
        return None

    def get_replic(self, last_message, messages, intens_dict, feelings, prev_scheme, current_scheme):
        """
        Генерирует ответ тьютора с учетом эмоционального состояния
        
        Args:
            last_message (str): Последняя реплика студента
            messages (list): История диалога
            intens_dict (dict): Словарь интенций
            feelings (np.array): Вектор эмоций
            prev_scheme (int): Предыдущий этап
            current_scheme (int): Текущий этап
            
        Returns:
            str: Ответ тьютора или сообщение об ошибке
        """
        # Формируем профиль студента
        rlt = [(intens_dict[i if val > -0.05 else -i], val) 
              for i, val in enumerate(feelings, start=1)]
        
        student_profile = "Характеристика студента:\n"
        for idx, (trait, value) in enumerate(rlt, start=1):
            student_profile += f"Студент {trait}\n"
            if value < -0.05:
                student_profile += f"Требуется коррекция: {trait}\n"

        # Добавляем сообщение о переходе между этапами
        transition_msg = ""
        if current_scheme - prev_scheme == 1:
            if current_scheme == 2:
                transition_msg = hlp.from1to2
            elif current_scheme == 3:
                transition_msg = hlp.from2to3
            elif current_scheme == 4:
                transition_msg = hlp.from3to4
        else:
            transition_msg = f"Вы находитесь на этапе {current_scheme + 1}"

        # Формируем полный промпт
        prompt = f"""
            Последняя реплика: {last_message}
            {student_profile}
            {transition_msg}
            Сгенерируй ответ (до 150 слов), учитывая профиль студента.
        """

        messages_opt = messages.copy()
        messages_opt.append({"role": "user", "content": prompt})

        body = {
            'model': 'deepseek-chat',
            'messages': messages_opt,
            'temperature': 0.7,  # Средняя температура для креативности
            'max_tokens': 300    # Ограничение длины ответа
        }

        result = self._make_api_request("/chat/completions", body)
        if result:
            return result["choices"][0]["message"]["content"]
        return "Не удалось получить ответ от API"

    def get_dummy_replic(self, messages):
        """
        Упрощенная версия генерации ответа (для тестов)
        
        Args:
            messages (list): История диалога
            
        Returns:
            str: Ответ тьютора или сообщение об ошибке
        """
        body = {
            'model': 'deepseek-chat',
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 300
        }
        
        result = self._make_api_request("/chat/completions", body)
        if result:
            return result["choices"][0]["message"]["content"]
        return "Ошибка соединения с API"

    def get_brain_status(self, messages, last_message, current_scheme):
        """
        Проверяет условия перехода между этапами
        
        Args:
            messages (list): История диалога
            last_message (str): Последняя реплика
            current_scheme (int): Текущий этап (0-3)
            
        Returns:
            str: "да" или "нет" или None при ошибке
        """
        prompts = {
            0: f"Является ли это согласием начать занятие: {last_message}. Ответ: да/нет",
            1: f"Это корректный outline? {last_message}. Ответ: да/нет",
            2: f"Это завершенное эссе? {last_message}. Ответ: да/нет"
        }
        
        if current_scheme not in prompts:
            return None

        messages_opt = messages.copy()
        messages_opt.append({"role": "user", "content": prompts[current_scheme]})

        body = {
            'model': 'deepseek-chat',
            'messages': messages_opt,
            'temperature': 0.1,  # Низкая температура для бинарных ответов
            'max_tokens': 10     # Ограничение на короткий ответ
        }

        result = self._make_api_request("/chat/completions", body)
        if result:
            return result["choices"][0]["message"]["content"].lower().strip()
        return None