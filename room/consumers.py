import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from django.utils.timesince import timesince
from django.utils import timezone
from django.contrib.auth import get_user_model
User = get_user_model()

from .models import Message, Room


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_title = self.scope['url_route']['kwargs']['room_title']
        self.room_group_name = f'chat_{self.room_title}'
        self.active_users = set()


        user_id = self.scope["user"].id

        self.active_users.clear()

        await self.save_user_to_room(user_id)

        await self.channel_layer.group_add(
            self.room_group_name, 
            self.channel_name
        ) 

        await self.accept()
        self.room = await self.get_room(self.room_title)

        self.active_users.add(self.scope['user'].username)
        await self.send_active_users([self.scope['user'].username])

    async def user_joined(self, event):
        username = event.get('username')
        self.active_users.add(username)
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'username': username  
        }))
        await self.send_active_users_to_room(list(self.active_users))

    async def user_left(self, event):
        username = event.get('username')
        self.active_users.discard(username)
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'username': username
        }))
        await self.send_active_users_to_room(list(self.active_users))

    async def disconnect(self, close_code):
        username = self.scope['user'].username
        self.active_users.discard(username)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_left",
                'username': username
            }
        )
        await self.send_active_users_to_room(list(self.active_users))

    async def get_active_users(self):
        return list(self.active_users)

    
    async def send_active_users(self, active_users):
        await self.send(text_data=json.dumps({
            'type': 'active_users',
            'users': active_users
        }))

    async def send_active_users_to_room(self, active_users):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'update_active_users',
                'active_users': active_users
            }
        )
    async def update_active_users(self, event):
        active_users = event['active_users']
        await self.send(text_data=json.dumps({
            'type': 'active_users',
            'users': active_users
        }))


    async def save_user_to_room(self, user_id):
        user = await sync_to_async(User.objects.get)(id=user_id)
        try:
            room = await sync_to_async(Room.objects.get)(title=self.room_title)
        except Room.DoesNotExist:
            return
        
        await sync_to_async(room.connect_user)(user)

        active_users = await self.get_active_users()
        await self.send_active_users_to_room(active_users)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'username': user.username
            }
        )

    async def get_room(self, room_title):
        return await sync_to_async(Room.objects.get)(title=room_title)

    
    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.get('command')
        if command == 'get_active_users':
            active_users = await self.get_active_users()
            await self.send_active_users(active_users)

        if 'type' in data:
            type = data['type']
            message = data['message']
            username = data['username']
            room_title = data['room']
            profile_image_url = data.get('profile_image_url')
            room = await self.get_room(room_title)

            if type == 'message':
                await self.save_message(username, room, message)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'username': username,
                        'room': room_title,
                        'timestamp': timezone.now().isoformat(),
                        'profile_image_url': profile_image_url,
                    }
                )
            if type == 'writing_active' or type == 'writing_inactive':
                await self.channel_layer.group_send(
                    self.room_group_name, {
                        'type': 'typing_status',
                        'message': message,
                        'username': username,
                        'room': room_title,
                        'typing': type == 'writing_active',
                    }
                )
            
        else:
            error_message = {
            'error': 'Field "type" is missing in the message data.'
            }
            
            
    async def chat_message(self, event):
        type = event['type']
        message = event['message']
        username = event['username']
        room_title = event['room']
        timestamp = event['timestamp']
        profile_image_url = event.get('profile_image_url')

        await self.send(text_data=json.dumps({
            'type': type,
            'message': message,
            'username': username,
            'timestamp': timestamp,
            'room': room_title,
            'profile_image_url': profile_image_url,
        }))

    async def typing_status(self, event):
        type = event['type']
        message = event['message']
        username = event['username']
        room_title = event['room']

        await self.send(text_data=json.dumps({
            'type': type,
            'message': message,
            'username': username,
            'room': room_title,
        }))

    @sync_to_async
    def save_message(self, username, room, message):
        user = User.objects.get(username=username)
        room = Room.objects.get(id=room.id)

        Message.objects.create(user=user, room=room, content=message)





