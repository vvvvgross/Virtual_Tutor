// Генерация уникального ID клиента на основе текущего времени
const client_id = Date.now()

// Создание WebSocket соединения с локальным сервером (версия для морального модуля)
let web_socket = new WebSocket(`ws://127.0.0.1:8000/test_2/ws/${client_id}`);
// Альтернативный вариант подключения к удаленному серверу (закомментирован)
// let web_socket = new WebSocket(`ws://bica-project.tw1.ru/test/ws/${client_id}`);

// Обработчик успешного открытия соединения
web_socket.onopen = () => {
    console.log('WebSocket Connection established');
};

// Обработчик входящих сообщений от сервера
web_socket.onmessage = (event) => {
    // Парсинг полученных данных JSON
    const response = JSON.parse(event.data);
    console.log(response)
    // Скрытие индикатора набора и добавление сообщения в чат
    hideTypingIndicator()
    addMessage(response.content, false); // false - сообщение от тьютора
};

// Получение DOM-элементов
const dialogEditor = document.getElementById('dialogEditor');
const essayEditor = document.getElementById('essayEditor');
const chatMessages = document.getElementById('chatMessages');
const typingIndicator = document.querySelector('.typing-indicator');

// Показать индикатор "тьютор печатает"
function showTypingIndicator() {
    typingIndicator.style.display = 'block';
    // Автоматическая прокрутка чата вниз
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Скрыть индикатор набора
function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

// Добавить сообщение в чат
// Параметры:
// - message: текст сообщения
// - isUser: флаг (true - сообщение от пользователя, false - от тьютора)
function addMessage(message, isUser = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'tutor'}`;
    messageDiv.textContent = message;
    // Вставка сообщения перед индикатором набора
    chatMessages.insertBefore(messageDiv, typingIndicator);
    // Автопрокрутка к новому сообщению
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
    
// Отправить сообщение в диалоге
async function submitDialog() {
    const message = dialogEditor.value;
    if (!message.trim()) return; // Игнорировать пустые сообщения

    // Добавить сообщение пользователя в чат
    addMessage(message, true);
    dialogEditor.value = ''; // Очистить поле ввода
    showTypingIndicator(); // Показать индикатор набора
    
    try {
        // Проверить состояние соединения
        if (web_socket.readyState === WebSocket.OPEN) {
            const data_dialog = {
                type: 'chat', // Тип сообщения - чат
                content: message,
                timestamp: new Date().toISOString() // Временная метка
            };
            // Отправить данные через WebSocket
            web_socket.send(JSON.stringify(data_dialog));
            console.log(data_dialog.content)
        }
    } catch (error) {
        hideTypingIndicator();
        console.error('Error submitting dialog:', error);
        alert('Error submitting dialog. Please try again.');
    }
}
    
// Отправить эссе на проверку
async function submitEssay() {
    showTypingIndicator(); // Показать индикатор набора
    try {
        if (web_socket.readyState === WebSocket.OPEN) {
            const data_essay = {
                type: 'essay', // Тип сообщения - эссе
                content: essayEditor.value,
                timestamp: new Date().toISOString()
            };
            web_socket.send(JSON.stringify(data_essay));
            console.log(data_essay.content)
        }
    } catch (error) {
        hideTypingIndicator();
        console.error('Error submitting essay:', error);
        alert('Error submitting essay. Please try again.');
    }
}
    
// Инициализация при загрузке страницы
window.addEventListener('load', () => {
    // Добавить приветственное сообщение от тьютора
    addMessage('Здравствуйте! Я ваш виртуальный тьютор. Чем могу помочь?', false);
});
    
// Обработчик нажатия Enter в поле диалога
dialogEditor.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Предотвратить перенос строки
        submitDialog(); // Отправить сообщение
    }
});