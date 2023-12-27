import requests
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ldap3 import Server, Connection, ALL
from datetime import datetime, timedelta
from .forms import LoginForm, AssignUserForm, MailingForm, StatusForm, UserProfileForm
from .models import *
from .utils import import_students_from_excel
from .ldap_check import check_ad_credentials
from telegram import Bot

def home(request):
    form = LoginForm(request.POST or None)
    advisors = None
    user_profile = None
    total_questions = open_questions = closed_questions = None
    start_date_str = end_date_str = None

    if request.user.is_authenticated:
        user = request.user

        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() + timedelta(days=1) if end_date_str else None
        except (ValueError, TypeError):
            start_date = end_date = None

        advisor_group = Group.objects.get(name='Advisor')
        main_advisor_group = Group.objects.get(name='Main Advisor')

        # Создаем запросы для каждой группы
        advisor_users = User.objects.filter(groups=advisor_group)
        main_advisor_users = User.objects.filter(groups=main_advisor_group)

        all_advisors = advisor_users | main_advisor_users

        if start_date and end_date:
            advisors = all_advisors.annotate(
                closed_count=Count('assigned_questions', filter=Q(assigned_questions__status='CLOSED', assigned_questions__created_at__range=(start_date, end_date))),
                in_process_count=Count('assigned_questions', filter=Q(assigned_questions__status='IN_PROCESS', assigned_questions__created_at__range=(start_date, end_date))),
                new_count=Count('assigned_questions', filter=Q(assigned_questions__status='NEW', assigned_questions__created_at__range=(start_date, end_date))),
                main_advisor_count=Count('assigned_questions', filter=Q(assigned_questions__status='MAIN_ADVISOR', assigned_questions__created_at__range=(start_date, end_date))),
            )
        else:
            advisors = all_advisors.annotate(
                closed_count=Count('assigned_questions', filter=Q(assigned_questions__status='CLOSED')),
                in_process_count=Count('assigned_questions', filter=Q(assigned_questions__status='IN_PROCESS')),
                new_count=Count('assigned_questions', filter=Q(assigned_questions__status='NEW')),
                main_advisor_count=Count('assigned_questions', filter=Q(assigned_questions__status='MAIN_ADVISOR')),
            )

        questions_query = Question.objects.all()
        if start_date and end_date:
            questions_query = questions_query.filter(created_at__range=(start_date, end_date))

        total_questions = questions_query.count()
        open_questions = questions_query.exclude(status='CLOSED').count()
        closed_questions = questions_query.filter(status='CLOSED').count()

        user_profile = None
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            pass

    # вход через ад
    AD_SERVER = '10.10.1.2'
    if request.method == 'POST' and not request.user.is_authenticated:
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            if "@almau.edu.kz" not in username:
                username += "@almau.edu.kz"

            if check_ad_credentials(AD_SERVER,username, password):
                request.session['is_authenticated'] = True
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
        'user': request.user, 
        'advisors': advisors,
        'user_profile': user_profile,
        'total_questions': total_questions,
        'open_questions': open_questions,
        'closed_questions': closed_questions,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'form': form,
    }
    return render(request, 'main_page/home.html', context)


@login_required
def show_questions(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

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
        'user_profile': user_profile
    }
    
    return render(request, 'requests/questions.html', context)

@login_required
def get_questions_json(request):
    search_query = request.GET.get('search', '')
    assigned_user_filter = request.GET.get('assigned_user', '')
    status_filter = request.GET.get('status', '')

    questions = Question.objects.all().order_by('-created_at')
    
    if search_query:
        questions = questions.filter(student__full_name__icontains=search_query)
    
    if assigned_user_filter:
        questions = questions.filter(assigned_user__username__icontains=assigned_user_filter)
    
    if status_filter:
        questions = questions.filter(status=status_filter)

    assigned_users = User.objects.filter(assigned_questions__isnull=False).distinct()
    status_choices = Question.STATUS_CHOICES
    
    page = request.GET.get('page', 1)
    paginator = Paginator(questions, 20)
    
    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        questions = paginator.page(1)
    except EmptyPage:
        questions = paginator.page(paginator.num_pages)
    
    questions_data = []
    for question in questions:
        if question.assigned_user:
            assigned_user_full_name = f"{question.assigned_user.username}"
        else:
            assigned_user_full_name = "Не назначен"

        if question.conversation:
            sorted_conversation = sorted(
                question.conversation, 
                key=lambda x: datetime.strptime(x['timestamp'], '%H:%M, %d/%m/%Y'),
                reverse=True
            )
            last_message = sorted_conversation[0]['text']
            last_message_time = sorted_conversation[0]['timestamp']
        else:
            last_message = "N/A"
            last_message_time = question.created_at.strftime('%H:%M, %d/%m/%Y')


        questions_data.append({
            'id': question.id,
            'student': question.student.full_name,
            'status_text': 'Новая' if question.status == 'NEW' else 'В обработке' if question.status == 'IN_PROCESS' else 'У главы ЭЦ' if question.status == 'MAIN_ADVISOR' else 'Закрыта',
            'status_color': '#007cb9' if question.status == 'NEW' else '#f96d00' if question.status == 'IN_PROCESS' else '#ff0000' if question.status == 'MAIN_ADVISOR' else '#42b883',
            'is_closed': question.status == 'CLOSED',
            'created_at': question.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'assigned_user': assigned_user_full_name,
            'last_message': last_message,
            'last_message_time': last_message_time,
        })

    questions_data.sort(key=lambda x: datetime.strptime(x['last_message_time'], '%H:%M, %d/%m/%Y'), reverse=True)

    
    return JsonResponse({
        'questions': questions_data,
        'paginator': paginator.num_pages,
        'assignedUser': [user.username for user in assigned_users],
        'status': [{'value': status[0], 'display': status[1]} for status in status_choices],
    })

@login_required
def get_total_questions_count(request):
    total_questions_count = Question.objects.all().count()
    return JsonResponse({'total_questions_count': total_questions_count})

@login_required
def get_chat_data(request, question_id):
    question = Question.objects.filter(id=question_id).first()
    if not question:
        return JsonResponse({'error': 'Вопрос не найден.'}, status=404)

    conversation_data = [
        {
            'text': entry['text'],
            'timestamp': entry['timestamp'],
            'type': entry['type']
        } for entry in question.conversation
    ] if question.conversation else []

    return JsonResponse({'conversation': conversation_data})

@login_required
def view_question(request, question_id):
    user_profile = UserProfile.objects.get(user=request.user)

    question = get_object_or_404(Question, id=question_id)
    quickMessages = QuickMessage.objects.all()

    # Инициализируем форму здесь, чтобы она была доступна в любом случае
    assign_user_form = AssignUserForm()
    status_form = StatusForm()

    if request.method == 'POST':
        # Различаем тип POST-запроса по наличию определенных параметров
        if 'answer' in request.POST:
            answer_text = request.POST.get('answer')

            current_time = timezone.now().strftime("%H:%M, %d/%m/%Y")
            answer = {'type': 'answer', 'text': answer_text, 'timestamp': current_time}
            question.conversation.append(answer)
            question.answered_at = timezone.now()
            question.answer = answer_text
            if question.status == 'MAIN_ADVISOR':
                question.status = 'MAIN_ADVISOR'
            else:
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

        elif 'status_form' in request.POST:
            status_form = StatusForm(request.POST)
            if status_form.is_valid():
                selected_status = status_form.cleaned_data.get('status')
                if question and selected_status:
                    question.status = selected_status
                    question.save()
                    return HttpResponseRedirect(request.path_info)


    return render(
        request, 
        'requests/question_chat.html', 
        {
            'question': question, 
            'quickMessages': quickMessages, 
            'assign_user_form': assign_user_form,
            'user_profile': user_profile,
            'status_form': status_form,
        }
    )

# @login_required
def fetch_ldap_entries():
    server = Server('10.10.1.2', get_info=ALL)
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
    user_profile = UserProfile.objects.get(user=request.user)

    search_query = request.GET.get('search_query', '')
    course_filter = request.GET.get('course_filter', '')
    gender_filter = request.GET.get('gender_filter', '')
    department_filter = request.GET.get('department_filter', '')

    if search_query:
        students = students.filter(
            Q(full_name__icontains=search_query) |
            Q(specialty__icontains=search_query) |
            Q(school__icontains=search_query)
        )

    if course_filter:
        students = students.filter(course=course_filter)

    if gender_filter:
        students = students.filter(gender=gender_filter)

    if department_filter:
        students = students.filter(department=department_filter)

    if 'submit' in request.POST:
        form = MailingForm(request.POST, request.FILES)
        if form.is_valid():
            selected_students = form.cleaned_data.get('students')
            
            if not selected_students:
                messages.error(request, 'Не выбран ни один студент для рассылки.')
            else:
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
        
    context = {
        'form': form,
        'students': students,
        'user_profile': user_profile,
        'search_query': search_query,
        'course_filter': course_filter,
        'gender_filter': gender_filter,
        'department_filter': department_filter,
        'filters_applied': any([search_query, course_filter, gender_filter, department_filter])
    }

    return render(request, 'main_page/send_mailing.html', context)


@login_required
def update_profile(request):
    # Создаем UserProfile, если он не существует
    UserProfile.objects.get_or_create(user=request.user)
    user_profile = UserProfile.objects.get(user=request.user)


    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            return redirect('/')
    else:
        form = UserProfileForm(instance=request.user.userprofile)

    return render(request, 'main_page/profile.html', {'form': form, 'user_profile': user_profile})

# скрипт для выгрузки студентов


# file_path = 'uploads/students.xlsx'
# import_students_from_excel(file_path)
@login_required
def import_students_view(request):
    if request.method == "POST":
        file_path = 'uploads/students.xlsx'
        import_students_from_excel(file_path)
        return HttpResponse("Студенты были успешно импортированы.")
    else:
        return render(request, 'main_page/import_students.html')

def logout_request(request):
    logout(request)
    return redirect('home')