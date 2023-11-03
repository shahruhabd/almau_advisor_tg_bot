from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from .consumers import QuestionConsumer  # Убедитесь, что у вас есть consumer с таким именем

websocket_urlpatterns = [
    path('ws/questions/', QuestionConsumer.as_asgi()),  # WebSocket к этому URL будет подключаться
]

application = ProtocolTypeRouter({
    'websocket': URLRouter(websocket_urlpatterns),
})