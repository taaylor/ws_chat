from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
from .models import ChatGroup, GroupMessage
import json

class ChatroomConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user'] # получаем текущего пользователя по ключу из сессии Http
        if self.user.is_anonymous:
            self.close()
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name']
        self.chatroom = get_object_or_404(ChatGroup, group_name=self.chatroom_name)

        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name,  # Название группы (комнаты чата), к которой подключается текущий пользователь.
            self.channel_name  # Уникальный идентификатор WebSocket-соединения для этого пользователя, автоматически сгенерированный сервером.
        )

        # добавление и обновление количества пользователей в сети.
        if self.user not in self.chatroom.users_online.all():
            self.chatroom.users_online.add(self.user)
            self.update_online_count()
        

        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name,
            self.channel_name
        )
        if self.user in self.chatroom.users_online.all():
            self.chatroom.users_online.remove(self.user)
            self.update_online_count()

    def receive(self, text_data=None):
        # text_data содержит данные, полученные по WebSocket (обычно в виде строки JSON).
        text_data_json = json.loads(text_data)  # Преобразование строки JSON в словарь Python.

        # Извлекаем тело сообщения (текст, который отправил пользователь).
        body = text_data_json['body']

        # Создаем новый объект сообщения в базе данных, используя модель GroupMessage.
        message = GroupMessage.objects.create(
            body=body,  # Текст сообщения.
            author=self.user,  # Автор сообщения - текущий пользователь.
            group=self.chatroom  # Комната (группа) чата, к которой относится сообщение.
        )

        # Создаем "событие", которое будет отправлено по каналу для всех участников группы.
        event = {
            'type': 'message_handler',  # Указываем, какой метод будет вызван на стороне получателя.
            'message_id': message.id  # Передаем ID сообщения, чтобы позже его можно было получить из базы.
        }

        # Отправляем событие в канал для всей группы (чат-комнаты).
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name,  # Имя группы (комнаты), в которой должны получить сообщение все пользователи.
            event  # Событие, которое будет обработано методом message_handler.
        )


    def message_handler(self, event):
        # Извлекаем ID сообщения из события.
        message_id = event['message_id']

        # Получаем объект сообщения из базы данных по его ID.
        message = get_object_or_404(GroupMessage, id=message_id)

        # Подготавливаем данные для шаблона (рендеринга).
        context_data = {
            'message': message,  # Само сообщение.
            'user': self.user,  # Текущий пользователь.
        }

        # Рендерим HTML для сообщения, используя шаблон 'chat_message_p.html'.
        html = render_to_string('a_rtchat/partials/chat_message_p.html', context=context_data)

        # Отправляем сгенерированный HTML обратно клиенту через WebSocket.
        self.send(text_data=html)

    def update_online_count(self):
        online_count = self.chatroom.users_online.count() - 1
        event = {
            'type': 'online_count_handler',
            'online_count': online_count
        }
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )

    def online_count_handler(self, event):
        online_count = event['online_count']

        context_data = {
            'online_count': online_count,
        }
        html = render_to_string('a_rtchat/partials/online_count.html', context=context_data)
        self.send(text_data=html)

            
