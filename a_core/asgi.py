import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack

# Устанавливаем настройку для Django, чтобы использовать её при загрузке приложения.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'a_core.settings')

# Создаем ASGI-приложение для обработки стандартных HTTP-запросов.
django_asgi_app = get_asgi_application()

from a_rtchat import routing

# Приложение ASGI, которое будет обрабатывать разные типы подключений, такие как HTTP и WebSocket.
application = ProtocolTypeRouter({
    # Для HTTP запросов используется стандартное Django ASGI-приложение.
    'http': django_asgi_app,

    # Для WebSocket запросов:
    'websocket': AllowedHostsOriginValidator(  # Проверяет, что WebSocket запросы приходят с разрешенных хостов.
        AuthMiddlewareStack(  # Оборачивает WebSocket в middleware для обработки авторизации.
            URLRouter(routing.websocket_urlpatterns)  # Определяет маршрутизацию для WebSocket URL-ов.
        )
    )
})
