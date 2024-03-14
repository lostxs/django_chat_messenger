from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Room, Message

@login_required
def rooms(request):
    rooms = Room.objects.all()

    return render(request, 'room/rooms.html', {'rooms': rooms})

@login_required
def room(request, title):
    room = Room.objects.get(title=title)
    messages = Message.objects.filter(room=room)

    return render(request, 'room/room.html', {'room': room, 'messages': messages})





