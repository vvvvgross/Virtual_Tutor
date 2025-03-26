from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, TypeAdapter
from virtual_tutor import VirtualTutor, DummyVirtualTutor
import helper as hlp
import uvicorn
import json
import os

# Кастомный класс для отключения кэширования статических файлов
class StaticFilesWithoutCaching(StaticFiles):
    def is_not_modified(self, *args, **kwargs) -> bool:
        """Всегда возвращает False, отключая кэширование"""
        return False

# Модель для WebSocket сообщений
class WssItem(BaseModel):
    type: str      # Тип сообщения ('chat' или 'essay')
    content: str   # Текст сообщения
    timestamp: str # Временная метка ISO

app = FastAPI()

@app.get("/")
def read_root():
    """Корневой endpoint для проверки работы сервера"""
    return {"message": "Welcome to the Virtual Tutor Server!"}

# Менеджер WebSocket соединений
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []  # Список активных соединений

    async def connect(self, websocket: WebSocket):
        """Добавляет новое соединение"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        """Удаляет соединение"""
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Отправляет сообщение конкретному клиенту"""
        await websocket.send_json(message)

manager = ConnectionManager()

# WebSocket endpoint для dummy-режима
@app.websocket("/test_1/ws/{client_id}")
async def dummy_websocket_endpoint(websocket: WebSocket, client_id: int):
    """Обработчик WebSocket для упрощенного тьютора"""
    await manager.connect(websocket)
    try:
        virtual_tutor = DummyVirtualTutor(client_id)
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_text()
            data_dict = json.loads(data)
            data_model = TypeAdapter(WssItem).validate_python(data_dict)
            
            # Генерируем ответ
            actor_replic = virtual_tutor.generate_answer(data_model.content)
            data_model.content = actor_replic
            
            # Отправляем ответ
            await manager.send_personal_message(data_model.model_dump(), websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# WebSocket endpoint для полноценного тьютора
@app.websocket("/test_2/ws/{client_id}")
async def moral_websocket_endpoint(websocket: WebSocket, client_id: int):
    """Обработчик WebSocket для тьютора с моральными схемами"""
    await manager.connect(websocket)
    try:
        virtual_tutor = VirtualTutor(client_id)
        while True:
            data = await websocket.receive_text()
            data_dict = json.loads(data) 
            data_model = TypeAdapter(WssItem).validate_python(data_dict)
            
            actor_replic = virtual_tutor.generate_answer(data_model.content)
            data_model.content = actor_replic
            
            await manager.send_personal_message(data_model.model_dump(), websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Настройка статических файлов для интерфейсов

# Получаем абсолютные пути к папкам с интерфейсами
ui_dummy_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../ui_dummy"))
ui_moral_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../ui_moral"))

# Монтируем статические файлы
app.mount("/test_1", StaticFilesWithoutCaching(directory=ui_dummy_path, html=True), name="dummy_static")
app.mount("/test_2", StaticFilesWithoutCaching(directory=ui_moral_path, html=True), name="moral_static")

# Запуск сервера
if __name__ == "__main__":
    config = hlp.load_config()
    if config["run_mode"] == "local":
        # Локальный режим с авто-перезагрузкой
        uvicorn.run(
            "test_server:app",
            host=config["running"]["local"]["host"],
            port=config["running"]["local"]["port"],
            reload=True
        )
    else:
        # Продакшен режим
        uvicorn.run(
            "test_server:app",
            host=config["running"]["server"]["host"],
            port=config["running"]["server"]["port"]
        )