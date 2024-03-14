from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.frontpage, name='frontpage'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('upload-profile-image/', views.upload_profile_image, name='upload_profile_image'),
    path('rooms/', include('room.urls')),
]