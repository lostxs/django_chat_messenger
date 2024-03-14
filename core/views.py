from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.core.mail import EmailMessage, send_mail


from core.forms import ProfileImageForm

from .models import Account
from .tokens import generate_token

from gfg import settings

from room.models import Room
# Create your views here.


User = get_user_model()

def frontpage(request):
    room = Room.objects.first()
    return render(request, 'core/frontpage.html', {'room': room})


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Проверка паролей
        if password1 != password2:
            return JsonResponse({'status': 'failed', 'message': 'Пароли не совпадают'})

        # Проверка существования пользователя с таким email
        if Account.objects.filter(email=email).exists():
            return JsonResponse({'status': 'failed', 'message': 'Пользователь с таким email уже существует'})

        # Создание пользователя
        user = Account.objects.create_user(username=username, email=email, password=password1)
        user.is_active = False
        user.save()

        # Подтверждение почты
        current_site = get_current_site(request)
        email_subject = "Подтверждение почты для PipiQ !"
        activate_url = reverse('activate', args=(urlsafe_base64_encode(force_bytes(user.pk)), generate_token.make_token(user)))
        activate_link = f"http://{current_site.domain}{activate_url}"
        message = f"Активируйте свой аккаунт, {user.username}. Ссылка для подтверждения: {activate_link}"
        email = EmailMessage(
            email_subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
        )
        email.fail_silently = True
        email.send()

        return JsonResponse({'status': 'success', 'message': 'Регистрация успешно завершена'})
    return render(request, 'signup.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        
        user = authenticate(username=username, password=password1)
        room = Room.objects.filter(users=user).first()
        
        if user:
            login(request, user)
            room_title = room.title
            redirect_url = reverse('room', kwargs={'title': room_title})
            return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
        else:
            return JsonResponse({'status': 'failed', 'message': 'Неверное имя пользователя или пароль'})
    
    return redirect('frontpage')


def signout(request):
    logout(request)
    messages.success(request, "Вы вышли из аккаунта")
    return redirect('frontpage')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and generate_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user, backend='django.contrib.auth.backends.AllowAllUsersModelBackend')
        messages.success(request, "Ваш аккаунт успешно активирован!!")
        return redirect('signin')
    else:
        return render(request, 'activation_failed.html')
    
@login_required
def upload_profile_image(request):
    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            # Возвращаем URL нового изображения профиля
            return JsonResponse({'status': 'success', 'profile_image_url': user.profile_image.url})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})
    return JsonResponse({'status': 'error', 'message': 'Метод не разрешен'})
