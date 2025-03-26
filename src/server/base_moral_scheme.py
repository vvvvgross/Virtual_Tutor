import math
import numpy as np
from oai_interface import Interface

class BaseMoralScheme:
    """Класс для работы с моральными схемами и эмоциональными векторами"""
    
    def __init__(self, base_intentions, changed_message=None, appraisals=None, feelings=None):
        """
        Инициализация моральной схемы.
        
        Args:
            base_intentions (dict): Словарь базовых интенций (позитивные и негативные)
            changed_message (str, optional): Сообщение при смене состояния. Defaults to None.
            appraisals (np.array, optional): Начальные значения вектора оценок. Defaults to None.
            feelings (np.array, optional): Начальные значения вектора чувств. Defaults to None.
        """
        # Базовые интенции (например: {1: "любознательность", -1: "безразличный"})
        self.base_intentions = base_intentions
        
        # Размер пространства интенций (вдвое больше, чем базовых, для позитивных/негативных)
        self.space_size = len(base_intentions)
        
        # Константы для формулы обновления:
        self.p_const = 0.03  # Скорость изменения чувств
        self.r_const = 0.1   # Скорость изменения оценок
        
        # Состояния (разница между позитивными и негативными компонентами)
        self.appraisals_state = np.zeros(self.space_size//2)
        self.feelings_state = np.zeros(self.space_size//2)
        
        # Интерфейс для работы с API
        self.oai_interface = Interface()
        
        # Инициализация векторов:
        # appraisals - как студент оценивает ситуацию
        # feelings - как студент реально чувствует
        self.appraisals = np.zeros(self.space_size) if appraisals is None else appraisals
        self.feelings = np.full(self.space_size, 0.5) if feelings is None else feelings
    
    def euc_dist(self, a, b):
        """
        Вычисление евклидова расстояния между векторами.
        
        Args:
            a (np.array): Первый вектор
            b (np.array): Второй вектор
            
        Returns:
            float: Расстояние между векторами
        """
        if len(a) != len(b):
            raise ValueError("Векторы должны иметь одинаковую длину")
        return math.sqrt(sum((a_i - b_i) ** 2 for a_i, b_i in zip(a, b)))
    
    def get_base_intentions(self):
        """Возвращает словарь базовых интенций"""
        return self.base_intentions
    
    def update_vectors(self, action):
        """
        Обновляет векторы оценок и чувств на основе нового действия.
        
        Args:
            action (np.array): Вектор нового действия от API
        """
        # Обновление оценок с учетом learning rate
        self.appraisals = (1 - self.r_const) * self.appraisals + self.r_const * action
        
        # Обновление чувств с учетом расхождения между оценками и текущими чувствами
        self.feelings = (1 - self.p_const) * self.feelings + self.p_const * (self.appraisals - self.feelings)
        
        # Расчет состояний как разницы между позитивными и негативными компонентами
        half = self.space_size // 2
        self.appraisals_state = self.appraisals[:half] - self.appraisals[half:]
        self.feelings_state = self.feelings[:half] - self.feelings[half:]
    
    # Методы доступа к состояниям:
    def get_appraisals(self): return self.appraisals
    def get_feelings(self): return self.feelings
    def get_appraisals_state(self): return self.appraisals_state
    def get_feelings_state(self): return self.feelings_state