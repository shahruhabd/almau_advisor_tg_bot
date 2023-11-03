from django import forms
from .models import Question, Mailing

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введите ваш логин',
            }
        ),
        label='',  # Убрать label
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Введите ваш пароль',
            }
        ),
        label='',  # Убрать label
    )

class AssignUserForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['assigned_user']


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ['students', 'message', 'file']