from datetime import timedelta
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404, render, redirect
import requests
from .models import *
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User, Group
from .forms import LoginForm, AssignUserForm, MailingForm
from .ldap_check import check_ad_credentials
from telegram import Bot
from ldap3 import Server, Connection, ALL
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.db.models import Count
from django.utils import timezone

def home(request):
    user = request.user
    advisor_group = Group.objects.get(name='Advisor')
    advisors = User.objects.filter(groups=advisor_group)
    total_questions = Question.objects.all().count()
    closed_questions = Question.objects.filter(status='CLOSED').count()
    new_questions = Question.objects.filter(status='NEW').count()

    today = timezone.now()
    start_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_day = start_day + timedelta(days=1)
    
    start_week = start_day - timedelta(days=start_day.weekday())
    end_week = start_week + timedelta(weeks=1)

    start_month = start_day.replace(day=1)
    end_month = (start_month + timedelta(days=31)).replace(day=1)

    daily_count = Question.objects.filter(created_at__range=(start_day, end_day)).count()
    weekly_count = Question.objects.filter(created_at__range=(start_week, end_week)).count()
    monthly_count = Question.objects.filter(created_at__range=(start_month, end_month)).count()

    # вход через ад
    AD_SERVER = 'ldap://dca.iab.kz'
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

    context = {
        'user': user, 
        'advisors': advisors,
        'total_questions': total_questions,
        'closed_questions': closed_questions,
        'new_questions': new_questions,
        'form': form,
        'daily_count': daily_count,
        'weekly_count': weekly_count,
        'monthly_count': monthly_count,
    }
    return render(request, 'main_page/home.html', context)

@login_required
def show_questions(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        questions = Question.objects.filter(student__full_name__icontains=search_query).order_by('-created_at')
    else:
        questions = Question.objects.all().order_by('-created_at')
        
    total_questions_count = Question.objects.all().count()
    
    for question in questions:
        question.last_message = question.conversation[-1]['text'] if question.conversation else "N/A"
        
    context = {
        'questions': questions,
        'total_questions_count': total_questions_count,
    }
    
    return render(request, 'requests/questions.html', context)

@login_required
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

# @login_required
def fetch_ldap_entries():
    server = Server('ldap://dca.iab.kz', get_info=ALL)
    conn = Connection(server, 'o.shevchenko@almau.edu.kz', 'vuB504')

    if not conn.bind():
        print("Could not bind to server.")
        return []

    # base_dn = 'OU=STUDENTS,DC=iab,DC=kz'
    base_dn = 'OU=UsersDoc,DC=iab,DC=kz'
    search_filter = '(objectClass=*)'

    conn.search(base_dn, search_filter, attributes=['cn', 'memberOf', 'sAMAccountName', 'userPrincipalName'])

    entries = []
    for entry in conn.entries:
        entries.append(entry.entry_attributes_as_dict)
    return entries

@login_required
def ad_list(request):
    entries = fetch_ldap_entries()
    return render(request, 'main_page/ad.html', {'entries': entries})

@login_required
def send_mailing(request):
    students = Student.objects.all()

    if request.GET:
        search_query = request.GET.get('search_query', '')
        course_filter = request.GET.get('course_filter', '')
        
        if search_query:
            students = students.filter(
                Q(full_name__icontains=search_query) |
                Q(specialty__name__icontains=search_query)
            )

        if course_filter:
            students = students.filter(course=course_filter)

        # Если нужно, объедините оба фильтра
        if search_query and course_filter:
            students = students.filter(
                Q(course=course_filter) &
                (Q(full_name__icontains=search_query) |
                Q(specialty__name__icontains=search_query))
            )

    if 'submit' in request.POST:
        form = MailingForm(request.POST, request.FILES)
        if form.is_valid():
            selected_students = form.cleaned_data.get('students')
            
            if not selected_students:
                messages.error(request, 'Не выбран ни один студент для рассылки.')
                return render(request, 'main_page/mailing.html', {'form': form, 'students': students})

            mailing = form.save()
            for student in mailing.students.all():
                chat_id = student.chat_id
                message = mailing.message
                token = '6381298802:AAFmZVISMBO9k9_T8MwweqBZFXoFuIGgOCg'
                send_message_url = f"https://api.telegram.org/bot{token}/sendMessage"
                
                try:
                    requests.post(send_message_url, data={'chat_id': chat_id, 'text': message}, verify=False)
                except requests.exceptions.RequestException as e:
                    messages.error(request, f'Ошибка при отправке сообщения: {e}')
                    continue
                
                if mailing.file:
                    file_path = mailing.file.path
                    send_file_url = f"https://api.telegram.org/bot{token}/sendDocument"
                    files = {'document': open(file_path, 'rb')}
                    try:
                        requests.post(send_file_url, data={'chat_id': chat_id}, files=files, verify=False)
                    except requests.exceptions.RequestException as e:
                        messages.error(request, f'Ошибка при отправке файла: {e}')
                        continue

            messages.success(request, 'Рассылка успешно отправлена!')
            return HttpResponseRedirect(reverse('send_mailing'))
        else:
            messages.error(request, 'Форма недействительна.')

    else:
        form = MailingForm()    

    return render(request, 'main_page/mailing.html', {'form': form, 'students': students})



