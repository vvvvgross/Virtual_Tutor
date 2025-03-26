// Генерация уникального ID клиента на основе текущего времени
const client_id = Date.now()

// Создание WebSocket соединения с локальным сервером
let web_socket = new WebSocket(`ws://127.0.0.1:8000/test_1/ws/${client_id}`);
// Альтернативный вариант подключения к удаленному серверу (закомментирован)
// let web_socket = new WebSocket(`ws://bica-project.tw1.ru/test/ws/${client_id}`);

// Обработчик открытия соединения WebSocket
web_socket.onopen = () => {
    console.log('WebSocket Connection established');
};

// Обработчик входящих сообщений через WebSocket
web_socket.onmessage = (event) => {
    // Парсинг полученных данных
    const response = JSON.parse(event.data);
    console.log(response)
    // Скрытие индикатора набора и добавление сообщения в чат
    hideTypingIndicator()
    addMessage(response.content, false);
};

// Получение DOM-элементов
const dialogEditor = document.getElementById('dialogEditor');
const essayEditor = document.getElementById('essayEditor');
const chatMessages = document.getElementById('chatMessages');
const typingIndicator = document.querySelector('.typing-indicator');

// Функция для отображения индикатора набора сообщения
function showTypingIndicator() {
    typingIndicator.style.display = 'block';
    // Прокрутка чата вниз
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Функция для скрытия индикатора набора сообщения
function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

// Функция добавления сообщения в чат
// Параметры:
// - message: текст сообщения
// - isUser: флаг, указывающий является ли отправитель пользователем (true) или тьютором (false)
function addMessage(message, isUser = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'tutor'}`;
    messageDiv.textContent = message;
    // Вставка сообщения перед индикатором набора
    chatMessages.insertBefore(messageDiv, typingIndicator);
    // Прокрутка чата вниз
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
    
// Функция отправки сообщения в диалоге
async function submitDialog() {
    const message = dialogEditor.value;
    if (!message.trim()) return; // Проверка на пустое сообщение

    // Добавление сообщения пользователя в чат
    addMessage(message, true);
    dialogEditor.value = ''; // Очистка поля ввода
    showTypingIndicator(); // Показать индикатор набора
    
    try {
        // Проверка состояния WebSocket соединения
        if (web_socket.readyState === WebSocket.OPEN) {
            const data_dialog = {
                type: 'chat', // Тип сообщения - чат
                content: message, // Текст сообщения
                timestamp: new Date().toISOString() // Временная метка
            };
            // Отправка данных через WebSocket
            web_socket.send(JSON.stringify(data_dialog));
            console.log(data_dialog.content)
        }
    } catch (error) {
        hideTypingIndicator();
        console.error('Error submitting dialog:', error);
        alert('Error submitting dialog. Please try again.');
    }
}
    
// Функция отправки эссе
async function submitEssay() {
    showTypingIndicator(); // Показать индикатор набора
    try {
        if (web_socket.readyState === WebSocket.OPEN) {
            const data_essay = {
                type: 'essay', // Тип сообщения - эссе
                content: essayEditor.value, // Текст эссе
                timestamp: new Date().toISOString() // Временная метка
            };
            // Отправка данных через WebSocket
            web_socket.send(JSON.stringify(data_essay));
            console.log(data_essay.content)
        }
    } catch (error) {
        hideTypingIndicator();
        console.error('Error submitting essay:', error);
        alert('Error submitting essay. Please try again.');
    }
}
    
// Обработчик загрузки страницы - добавляет приветственное сообщение
window.addEventListener('load', () => {
    addMessage('Здравствуйте! Я ваш виртуальный тьютор. Чем могу помочь?', false);
});
    
// Обработчик нажатия клавиши Enter в поле диалога
dialogEditor.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Предотвращение переноса строки
        submitDialog(); // Отправка сообщения
    }
});