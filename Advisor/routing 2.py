from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from Advisor.consumers import RequestConsumer

websocket_urlpatterns = [
    re_path(r"ws/requests/", RequestConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': URLRouter(websocket_urlpatterns),
})