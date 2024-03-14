from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.rooms, name='rooms'),
    path('<str:title>/', views.room, name='room'),
]