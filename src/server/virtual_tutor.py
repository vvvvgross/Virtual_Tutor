import numpy as np
import helper as hlp
import logging
from pathlib import Path
import os
from base_moral_scheme import BaseMoralScheme
from oai_interface import Interface

def create_logger(logger_name, log_dir, log_file):
    """
    Создает и настраивает логгер с записью в файл
    
    Args:
        logger_name (str): Уникальное имя логгера
        log_dir (str): Директория для логов
        log_file (str): Имя файла лога
        
    Returns:
        Logger: Настроенный объект логгера
    """
    # Создаем директорию если ее нет
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # Настройка обработчика для записи в файл
    handler = logging.FileHandler(
        os.path.join(log_dir, log_file),
        mode='w',
        encoding='utf-8'
    )
    
    formatter = logging.Formatter("%(asctime)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

class DummyVirtualTutor:
    """Упрощенная версия тьютора без анализа эмоций"""
    
    def __init__(self, id):
        """
        Инициализация dummy-тьютора
        
        Args:
            id (int): Уникальный ID сессии
        """
        self.client_id = id
        
        # История сообщений начинается с системного промпта
        self.messages = [{"role": "system", "content": hlp.start_promt_dvt}]
        
        # Интерфейс для работы с API
        self.oai_interface = Interface()
        
        # Настройка логгеров
        self.logger_dialog = create_logger(
            f"dialog_logger_{self.client_id}",
            f"../../logs_dummy/{self.client_id}",
            "dialog.log"
        )
        
        self.logger_essay = create_logger(
            f"essay_logger_{self.client_id}",
            f"../../logs_dummy/{self.client_id}",
            "essay.log"
        )
        
        # Запись в лог
        self.logger_dialog.info("Dummy tutor initialized")
        self.logger_essay.info("Essay logger initialized")
        
    def generate_answer(self, replic):
        """
        Генерирует ответ на реплику студента
        
        Args:
            replic (str): Текст реплики студента
            
        Returns:
            str: Ответ тьютора
        """
        # Добавляем реплику студента в историю
        self.messages.append({"role": "user", "content": replic})
        
        # Получаем ответ от API
        tutor_response = self.oai_interface.get_dummy_replic(self.messages)
        
        # Логируем диалог
        self.logger_dialog.info(f"Student: {replic}")
        self.logger_dialog.info(f"Tutor: {tutor_response}")
        
        return tutor_response

class VirtualTutor:
    """Основной класс тьютора с моральными схемами"""
    
    def __init__(self, id):
        """
        Инициализация тьютора с моральными схемами
        
        Args:
            id (int): Уникальный ID сессии
        """
        self.client_id = id
        
        # Настройка логгеров
        self.logger_dialog = create_logger(
            f"dialog_logger_{self.client_id}",
            f"../../logs_moral/{self.client_id}",
            "dialog.log"
        )
        
        self.logger_essay = create_logger(
            f"essay_logger_{self.client_id}",
            f"../../logs_moral/{self.client_id}",
            "essay.log"
        )
        
        self.logger_dialog.info("Moral tutor initialized")
        self.logger_essay.info("Essay logger initialized")

        # Инициализация моральных схем для каждого этапа:
        self.ms_list = [
            # Этап 1: Знакомство
            BaseMoralScheme(hlp.first_space, hlp.from1to2, feelings=hlp.feelings1),
            # Этап 2: Outline
            BaseMoralScheme(hlp.second_space, hlp.from2to3, feelings=hlp.feelings2),
            # Этап 3: Написание эссе
            BaseMoralScheme(hlp.third_space, hlp.from3to4, feelings=hlp.feelings3),
            # Этап 4: Оценка
            BaseMoralScheme(hlp.fourth_space, feelings=hlp.feelings4)
        ]
        
        # Текущее состояние
        self.last_replic = ""  # Последняя реплика студента
        self.prev_moral_id = 0  # Предыдущий этап
        self.cur_moral_id = 0   # Текущий этап
        self.messages = [{"role": "assistant", "content": hlp.start_promt_dvt}]
        self.schemes = [False, False, False, False]  # Флаги завершения этапов
        self.brain = [False, False, False, False]    # Флаги условий перехода

    def generate_answer(self, replic):
        """
        Основной метод генерации ответа с учетом моральных схем
        
        Args:
            replic (str): Реплика студента
            
        Returns:
            str: Ответ тьютора
        """
        # Сохраняем реплику
        self.last_replic = replic
        
        # Логируем текущее состояние
        self.logger_dialog.warning(f'Схемы: {self.schemes}')
        self.logger_dialog.warning(f'Переходы: {self.brain}')
        
        # Получаем текущие интенции и анализируем реплику
        intents = self.ms_list[self.cur_moral_id].get_base_intentions()
        action = self.ms_list[self.cur_moral_id].oai_interface.get_composition(intents, replic)
        
        if action is None:
            self.logger_dialog.error("API request failed")
            return "Не удалось связаться с сервером"
        
        # Обновляем векторы состояния
        self.ms_list[self.cur_moral_id].update_vectors(np.array(action))
        
        # Получаем текущие состояния
        appr_state = self.ms_list[self.cur_moral_id].get_appraisals_state()
        feel_state = self.ms_list[self.cur_moral_id].get_feelings_state()
        
        # Вычисляем расстояние между состояниями
        dist = self.ms_list[self.cur_moral_id].euc_dist(appr_state, feel_state)
        
        # Логируем состояния
        self.logger_dialog.warning(f'Appraisals: {self.ms_list[self.cur_moral_id].get_appraisals()}')
        self.logger_dialog.warning(f'Feelings: {self.ms_list[self.cur_moral_id].get_feelings()}')
        self.logger_dialog.warning(f'Distance: {dist}')
        
        # Проверяем условия перехода между этапами
        if self.cur_moral_id <= 2:  # Для этапов 0-2
            condition = self.ms_list[self.cur_moral_id].oai_interface.get_brain_status(
                self.messages, replic, self.cur_moral_id)
            
            self.logger_dialog.warning(f'Condition: {condition}')
            
            if condition and "да" in condition.lower():
                self.brain[self.cur_moral_id] = True
                self.cur_moral_id = min(self.cur_moral_id + 1, 3)  # Переход на след. этап
        
        # Проверка на достижение критической точки
        if dist < 0.25:
            self.schemes[self.cur_moral_id] = True
        
        # Сохраняем предыдущий этап
        self.prev_moral_id = self.cur_moral_id
        
        # Генерируем ответ с учетом разницы состояний
        diff = appr_state - feel_state
        reply = self.ms_list[self.cur_moral_id].oai_interface.get_replic(
            replic, self.messages, intents, diff, self.prev_moral_id, self.cur_moral_id)
        
        # Обновляем историю диалога
        self.messages.append({"role": "user", "content": replic})
        self.messages.append({"role": "assistant", "content": reply})
        
        # Логируем диалог
        self.logger_dialog.info(f"Student: {replic}")
        self.logger_dialog.info(f"Tutor: {reply}")
        
        return reply