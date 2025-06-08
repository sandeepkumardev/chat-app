import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.text import slugify

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # from .models import Room

        # try:
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        safe_room_name = slugify(self.room_name)
        self.room_group_name = f'chat_{safe_room_name}'
        # except Room.DoesNotExist:
        #     await self.close()
        #     return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': f'{self.scope["user"].first_name} joined the chat.',
                'username': 'System',
                'name': 'System'                
            }
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': f'{self.scope["user"].first_name} left the chat.',
                'username': 'System',
                'name': 'System'
            }
        )


    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']
        name = data['name'] or ''

        room = self.room_name

        await self.save_message(username, room, message)

        # Send message to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'name': name
            }
        )

    # Receive message from group
    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        name = event['name']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'name': name
        }))

    @database_sync_to_async
    def save_message(self, username, room, message):
        from .models import Room, Message
        from django.contrib.auth.models import User

        user = User.objects.get(username=username)
        room = Room.objects.get(slug=room)
        Message.objects.create(user=user, room=room, content=message)



class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        self.room_group_name = f"private_chat_{self.room_slug}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.send_system_message(f"Connected to private chat.")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender = self.scope["user"]

        # Save message
        await self.save_message(sender.username, self.room_slug, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": sender.username,
                "name": sender.first_name or sender.username,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "username": event["username"],
            "name": event["name"],
        }))

    async def send_system_message(self, message):
        await self.send(text_data=json.dumps({
            "message": message,
            "username": "System",
            "name": "System",
        }))

    from asgiref.sync import sync_to_async
    @sync_to_async
    def save_message(self, sender_username, room_slug, message):
        from django.contrib.auth import get_user_model
        from .models import PrivateChatMessage, PrivateRoom

        User = get_user_model()
        try:
            sender = User.objects.get(username=sender_username)
            room = PrivateRoom.objects.get(room_slug=room_slug)
            PrivateChatMessage.objects.create(sender=sender, room=room, content=message)
        except Exception as e:
            print("Error saving private message:", e)
