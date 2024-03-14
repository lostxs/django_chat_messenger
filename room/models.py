from django.db import models
from django.conf import settings

from asgiref.sync import sync_to_async

# Create your models here.

class Room(models.Model):
    title = models.CharField(max_length=255, unique=True, blank=False,)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, help_text="пользователи которые подключенны к чату")


    def connect_user(self, user):
        if not user in self.users.all():
            self.users.add(user)
            self.save()
        else:
            return False

 
    def disconnect_user(self, user):
        if user in self.users.all():
            self.users.remove(user)
            self.save()
        else:
            return False
    
    @property
    def group_name(self):
        return f'Room-{self.id}'
    
class MessageManager(models.Manager):
    def by_room(self, room):
        qs = Message.objects.filter(room=room).order_by("-timestamp")
        return qs
    
class Message(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(unique=False, blank=False)

    objects = MessageManager()

    def __str__(self):
        return self.content
    






