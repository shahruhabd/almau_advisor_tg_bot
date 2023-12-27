from django import forms
from django.contrib.auth.models import User, Group
from .models import Question, Mailing, UserProfile
from django.db.models import Q

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

class AssignUserForm(forms.Form):
    # Инициализируем форму с кастомным queryset для поля assigned_user
    def __init__(self, *args, **kwargs):
        super(AssignUserForm, self).__init__(*args, **kwargs)
        # Получаем группы
        advisor_group = Group.objects.get(name='Advisor')
        main_advisor_group = Group.objects.get(name='Main Advisor')
        # Формируем queryset с помощью Q-объектов
        self.fields['assigned_user'].queryset = User.objects.filter(
            Q(groups=advisor_group) | Q(groups=main_advisor_group)
        )

    # Здесь мы определяем поле формы
    assigned_user = forms.ModelChoiceField(
        queryset=User.objects.none(),  # Изначально нет пользователей
        empty_label="Выберите Эдвайзера"
    )


class StatusForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['status']


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ['students', 'message', 'file']


class UserProfileForm(forms.ModelForm):
    full_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введите ваше имя'
            }
        ),
        label='',
    )
    class Meta:
        model = UserProfile
        fields = ['full_name'] 
