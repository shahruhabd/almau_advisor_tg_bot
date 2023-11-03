import json
from channels.generic.websocket import AsyncWebsocketConsumer

class QuestionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "questions_default_room"  # Создаем имя группы

        # Присоединяемся к группе
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Отключаемся от группы
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def question_message(self, event):
        question = event['question']

        # Отправка сообщения в WebSocket
        await self.send(text_data=json.dumps({
            'question': question
        }))
