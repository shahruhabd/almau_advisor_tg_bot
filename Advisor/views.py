import datetime
from itertools import chain
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from .models import *
import requests
from django.contrib import messages
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from .forms import LoginForm, AssignUserForm
from .ldap_check import check_ad_credentials
from telegram import Bot
from ldap3 import Server, Connection, ALL


def home(request):
    user = request.user
    advisor_group = Group.objects.get(name='Advisor')
    advisors = User.objects.filter(groups=advisor_group)
    total_questions = Question.objects.all().count()
    context = {
        'user': user, 
        'advisors': advisors,
        'total_questions': total_questions
    }
    return render(request, 'main_page/home.html', context)

def login_success(request):
    return render(request, 'registration/login_success.html')


# вход через ад
AD_SERVER = 'ldap://dca.iab.kz'

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            if "@almau.edu.kz" not in username:
                username += "@almau.edu.kz"

            if check_ad_credentials(AD_SERVER,username, password):
                request.session['is_authenticated'] = True
                # Проверьте, существует ли пользователь в базе данных
                user, created = User.objects.get_or_create(username=username)
                
                if created:
                    user.set_password(password)
                    user.save()

                login(request, user)
                
                return redirect('/')
            else:
                form.add_error(None, 'Неверные учетные данные')
    else:
        form = LoginForm()
    return render(request, 'auth/login_ad.html', {'form': form})

def show_questions(request):
    questions = Question.objects.all()
    for question in questions:
        question.last_message = question.conversation[-1]['text'] if question.conversation else "N/A"

    return render(request, 'requests/questions.html', {'questions': questions})
    
def view_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    quickMessages = QuickMessage.objects.all()

    # Инициализируем форму здесь, чтобы она была доступна в любом случае
    assign_user_form = AssignUserForm()

    if request.method == 'POST':
        # Различаем тип POST-запроса по наличию определенных параметров
        if 'answer' in request.POST:
            answer_text = request.POST.get('answer')

            current_time = timezone.now().strftime('%H:%M')
            answer = {'type': 'answer', 'text': answer_text, 'timestamp': current_time}
            question.conversation.append(answer)
            question.answered_at = timezone.now()
            question.answer = answer_text
            question.status = 'IN_PROCESS'
            question.save()

            # Отправляем ответ в Telegram
            bot = Bot(token='6381298802:AAFmZVISMBO9k9_T8MwweqBZFXoFuIGgOCg')
            student = question.student
            chat_id = student.chat_id
            bot.send_message(chat_id, f'Ответ на ваш вопрос: {question.answer}')
        
            return HttpResponseRedirect(request.path_info)
        
        elif 'assign_user_form' in request.POST:
            assign_user_form = AssignUserForm(request.POST)
            if assign_user_form.is_valid():
                selected_user = assign_user_form.cleaned_data.get('assigned_user')
                if question and selected_user:
                    question.assigned_user = selected_user
                    question.save()
                    return HttpResponseRedirect(request.path_info)

    return render(
        request, 
        'requests/question_chat.html', 
        {'question': question, 'quickMessages': quickMessages, 'assign_user_form': assign_user_form}
    )

def fetch_ldap_entries():
    server = Server('ldap://dca.iab.kz', get_info=ALL)
    conn = Connection(server, 'o.shevchenko@almau.edu.kz', 'vuB504')

    if not conn.bind():
        print("Could not bind to server.")
        return []

    base_dn = 'OU=UsersDoc,DC=iab,DC=kz'
    search_filter = '(objectClass=*)'

    conn.search(base_dn, search_filter, attributes=['cn', 'memberOf', 'sAMAccountName', 'userPrincipalName'])

    entries = []
    for entry in conn.entries:
        entries.append(entry.entry_attributes_as_dict)
    return entries

def ad_list(request):
    entries = fetch_ldap_entries()
    return render(request, 'main_page/ad.html', {'entries': entries})