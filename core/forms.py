from django import forms
from .models import Account

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['profile_image']

    def clean_profile_image(self):
        profile_image = self.cleaned_data.get('profile_image', False)
        if profile_image:
            if profile_image.size > 10 * 1024 * 1024:  # Максимальный размер файла 10 МБ
                raise forms.ValidationError("Размер изображения слишком большой (максимум 10 МБ)")
            return profile_image
        else:
            raise forms.ValidationError("Не удалось загрузить изображение")