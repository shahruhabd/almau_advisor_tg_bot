from asyncio import Server
from http import server
import os
import django
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Almau_Advisor.settings")
django.setup()
import ldap3
from ldap3.core.exceptions import LDAPBindError
import ssl
import requests
from telegram.utils.request import Request

AD_SERVER = '10.10.1.2'

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
from django.conf import settings

from django.contrib.auth.models import User
from Advisor.models import Student, Specialty, FAQ, Question
from django.db.models import Count, Q
from helpdesk.models import Lecturer, HelpDeskUser, HelpDeskRequest

from datetime import datetime

def check_ad_credentials_stud(AD_SERVER, username, password):
    base_dn = 'OU=STUDENTS,DC=iab,DC=kz'
    search_filter = f'(userPrincipalName={username})'

    # Используйте DN и пароль, который работает для подключения
    # conn = ldap3.Connection(AD_SERVER, 's.abdugapar@almau.edu.kz', 'mjE024', auto_bind=True)
    try:
        conn = ldap3.Connection(AD_SERVER, username, password, auto_bind=True)
        if not conn.bind():
            print("Ошибка подключения к LDAP")
            return False

        if conn.search(base_dn, search_filter):
            print(f"Пользователь {username} найден")
            return True
        else:
            print("Пользователь не найден")
            return False
    except LDAPBindError:
        print("Неверные учетные данные")
        return False

def check_ad_credentials_teach(AD_SERVER, username, password):
    base_dn = 'OU=UsersDoc,DC=iab,DC=kz'
    search_filter = f'(userPrincipalName={username})'

    # Используйте DN и пароль, который работает для подключения
    # conn = ldap3.Connection(AD_SERVER, 's.abdugapar@almau.edu.kz', 'mjE024', auto_bind=True)
    try:
        conn = ldap3.Connection(AD_SERVER, username, password, auto_bind=True)
        if not conn.bind():
            print("Ошибка подключения к LDAP")
            return False

        if conn.search(base_dn, search_filter):
            print(f"Пользователь {username} найден")
            return True
        else:
            print("Пользователь не найден")
            return False
    except LDAPBindError:
        print("Неверные учетные данные")
        return False

#  base_dn = 'OU=STUDENTS,DC=iab,DC=kz'  -  dn для студентов
    
def start(update, context):
    message = update.message or update.callback_query.message

    current_user = context.user_data.get('user')
    current_role = context.user_data.get('role')
    context.user_data['user'] = current_user
    context.user_data['role'] = current_role
    
    if current_user is not None:
        username = current_user.username

        try:
            student = Student.objects.get(username=current_user)
            full_name = student.full_name
        except Student.DoesNotExist:
            full_name = None

        if full_name:
            message.reply_text(f'Привет 👋 {full_name}! Ваше главное меню.')
        else:
            message.reply_text(f'{username}. Ваше главное меню.')


        # ЕСЛИ СТУДЕНТ
        if current_user is not None and context.user_data.get('role') == 'student':
            keyboard = [
                [InlineKeyboardButton("Face ID 🆔", url='https://faceid.almau.edu.kz/')],
                [InlineKeyboardButton("Вопросы и ответы ❓", callback_data='faq')],
                [InlineKeyboardButton("Связь с эдвайзером 👩‍🏫", callback_data='ask_adviser')],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)

        # ЕСЛИ ПРЕПОД
        if current_user is not None and context.user_data.get('role') == 'teacher':
            try:
                helpdesk_user = HelpDeskUser.objects.get(user=current_user)
                keyboard = [
                    [InlineKeyboardButton("Новые заявки", callback_data='show_request')],
                    [InlineKeyboardButton("Мои заявки", callback_data='show_my_requests')],
                    [InlineKeyboardButton("Закрытые заявки", callback_data='show_closed_requests')],
                ]
            except HelpDeskUser.DoesNotExist:
                keyboard = [
                    [InlineKeyboardButton("Проблемы с оборудованием?", callback_data='create_request')]
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)

    else:
        update.message.reply_text('🦉')
        keyboard = [
            [InlineKeyboardButton("Студент 👨‍🎓", callback_data='student')],
            [InlineKeyboardButton("Преподаватель 👨‍🏫", callback_data='teacher')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text('Добро пожаловать! Выберите свою роль', reply_markup=reply_markup)
        return ConversationHandler.END

# ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
FAQ_QUESTION = range(1)
def faq_command(update, context):
    query = update.callback_query
    query.message.reply_text("Введите свой вопрос коротким хэш-тегом\n\nНапример: онай или военная кафедра или ритейк")
    query.answer()
    return FAQ_QUESTION

def handle_message(update, context):
    user_input = update.message.text

    # Поиск в FAQ
    matching_faqs = FAQ.objects.filter(Q(question__icontains=user_input) | Q(answer__icontains=user_input))

    if matching_faqs.exists():
        response = ''
        for i, faq in enumerate(matching_faqs):
            response += f"{i+1}. {faq.question}\n{faq.answer}\n\n"
        update.message.reply_text(f'{response}\n\n/start - главное меню')
    else:
        update.message.reply_text("По вашему запросу ничего не найдено.\n\n/start - главное меню")
    return ConversationHandler.END

# АВТОРИЗАЦИЯ ДЛЯ СТУДЕНТОВ
USERNAME, PASSWORD, FULL_NAME, COURSE, SPECIALTY, GENDER, DEPARTMENT = range(7)

def button(update, context):
    context.user_data.clear()
    query = update.callback_query
    query.answer()

    # Обработка выбора пользователя
    if query.data == 'student':
        context.user_data['role'] = 'student'
        context.user_data['chat_id'] = query.message.chat_id
        context.bot.send_message(chat_id=update.effective_chat.id, text="Студент? Пожалуйста, войдите здесь. Для отмены авторизации или смены роли нажмите\n/cancel")
        context.bot.send_message(chat_id=update.effective_chat.id, text="Введите ваш логин:")
        return USERNAME

def receive_username(update, context):
    username = update.message.text
    if "@almau.edu.kz" not in username:
        username += "@almau.edu.kz"
    context.user_data['auth_username'] = username
    update.message.reply_text("Введите ваш пароль:")
    return PASSWORD

def receive_password(update, context):
    username = context.user_data.get('auth_username')
    password = update.message.text

    if check_ad_credentials_stud(AD_SERVER, username, password):
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save()
        context.user_data['user'] = user

        # Используем поле username для связи с объектом Student
        student, student_created = Student.objects.get_or_create(username=username)
        student.chat_id = update.message.chat_id
        student.save()
        context.user_data['student'] = student

        # Проверяем, заполнены ли необходимые данные у студента
        if student_created or not student.has_all_required_data():
            update.message.reply_text('Авторизация прошла успешно ✅ Введите ваше ФИО.')
            return FULL_NAME
        else:
            update.message.reply_text('Авторизация прошла успешно ✅')
            start(update, context)
            return ConversationHandler.END
    else:
        update.message.reply_text('Неверные учетные данные.')
        context.user_data.clear()
        start(update, context)
        return ConversationHandler.END

def receive_full_name(update, context):
    full_name = update.message.text
    context.user_data['full_name'] = full_name
    keyboard = [['1', '2', '3', '4']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text("Выберите ваш курс:", reply_markup=reply_markup)
    return COURSE

def receive_course(update, context):
    course = update.message.text
    context.user_data['course'] = course
    # Отправка нумерованного списка специальностей
    specialties = Specialty.objects.all()
    specialty_list = {str(idx + 1): specialty for idx, specialty in enumerate(specialties)}
    context.user_data['specialty_list'] = specialty_list
    
    # Отправляем пользователю нумерованный список специальностей
    message_text = "Выберите вашу специальность, введя её номер:\n" + \
                   "\n".join([f"{index}. {spec.name}" for index, spec in specialty_list.items()])
    update.message.reply_text(message_text)
    return SPECIALTY

def receive_specialty(update, context):
    selection = update.message.text
    specialty_list = context.user_data.get('specialty_list', {})

    if selection.isdigit():
        selection_key = str(int(selection))
        if selection_key in specialty_list:
            specialty = specialty_list[selection_key]
            context.user_data['specialty'] = specialty.name
            # Переход к выбору гендера без дополнительных сообщений
            return receive_gender(update, context)
        else:
            update.message.reply_text("Пожалуйста, введите номер из списка.")
            return SPECIALTY
    else:
        update.message.reply_text("Пожалуйста, введите номер.")
        return SPECIALTY

def receive_gender(update, context):
    gender_text = update.message.text
    gender_map = {'Мужской': 'M', 'Женский': 'F'}
    gender = gender_map.get(gender_text, None)
    if gender is None:
        # Если пол не был выбран правильно, предложите выбрать еще раз
        reply_keyboard = [['Мужской', 'Женский']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        update.message.reply_text("Выберите ваш пол:", reply_markup=markup)
        return GENDER
    else:
        # Пол был выбран правильно, спросим отделение
        context.user_data['gender'] = gender
        reply_keyboard = [['Казахский', 'Русский', 'Английский']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        update.message.reply_text("Выберите ваше отделение:", reply_markup=markup)
        return DEPARTMENT

def receive_department(update, context):
    department_text = update.message.text
    department_map = {'Казахский': 'KZ', 'Русский': 'RU', 'Английский': 'EN'}
    department = department_map.get(department_text, None)
    if department is None:
        # Если отделение не было выбрано правильно, предложите выбрать еще раз
        reply_keyboard = [['Казахский', 'Русский', 'Английский']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        update.message.reply_text("Выберите ваше отделение:", reply_markup=markup)
        return DEPARTMENT
    else:
        # Отделение было выбрано правильно, сохраняем данные
        context.user_data['department'] = department
        save_student_data(context.user_data)
        update.message.reply_text("Спасибо, ваша информация сохранена.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

def save_student_data(user_data):
    # Получаем объект Student из user_data
    student = user_data['student']
    student.chat_id = user_data.get('chat_id')
    student.full_name = user_data['full_name']
    student.course = user_data['course']
    student.gender = user_data['gender']
    student.department = user_data['department']

    # Получаем объект Specialty по его названию
    specialty_name = user_data['specialty']
    specialty_obj, created = Specialty.objects.get_or_create(name=specialty_name)

    # Присваиваем объект Specialty полю specialty в объекте Student
    student.specialty = specialty_obj

    # Сохраняем объект Student
    student.save()

def cancel(update, context):
    context.user_data.clear()
    update.message.reply_text('Процесс был прерван. Если хотите начать снова, используйте команду /start.')
    return ConversationHandler.END

# ВОПРОС ЭДВАЙЗЕРУ
def ask_question(update, context):
    update.callback_query.message.reply_text('Пожалуйста, напишите ваш вопрос.')
    return TYPING_QUESTION  # Новое состояние для обработки ввода текста

TYPING_QUESTION = range(1)  
def handle_question_text(update, context):
    question_text = update.message.text
    student = context.user_data.get('student')

    # Проверяем, авторизован ли пользователь
    if not student:
        update.message.reply_text('Пожалуйста, сначала пройдите аутентификацию.')
        return

    # Определяем текст вопроса в зависимости от типа обновления
    text = update.message.text if update.message else update.callback_query.data

    # Получаем последний вопрос пользователя, который не закрыт
    question = Question.objects.filter(
        student=student, 
        status__in=['NEW', 'MAIN_ADVISOR', 'IN_PROCESS']
    ).last()

    # Если открытый вопрос уже существует, добавляем к нему сообщение
    if question:
        current_time = datetime.now().strftime('%H:%M, %d/%m/%Y')
        new_entry = {'type': 'question', 'text': text, 'timestamp': current_time}
        if question.conversation:
            question.conversation.append(new_entry)
        else:
            question.conversation = [new_entry]
        question.save()
        text_to_send = 'Ваше сообщение добавлено к текущему вопросу.'
    else:
        # Если открытых вопросов нет, создаем новый
        assigned_user = User.objects.filter(groups__name='Advisor').annotate(num_requests=Count('assigned_questions')).order_by('num_requests').first()
        new_question = Question.objects.create(
            student=student, 
            status='NEW', 
            conversation=[{
                'type': 'question',
                'text': text,
                'timestamp': datetime.now().strftime('%H:%M, %d/%m/%Y')
            }],
            assigned_user=assigned_user
        )
        text_to_send = 'Ваш вопрос зарегистрирован. Мы постараемся ответить как можно скорее.'

    update.message.reply_text(text_to_send) if update.message else update.callback_query.message.reply_text(text_to_send)

# Обработчик для не-текстовых сообщений
def handle_non_text_message(update, context):
    update.message.reply_text("Извините, я могу принимать только текстовые сообщения.")

# ЗАКРЫТИЕ ЧАТА
def close_chat(update, context):
    student = context.user_data.get('student')
    if student:
        open_question = Question.objects.filter(
            student=student,
            status__in=['NEW', 'IN_PROCESS', 'MAIN_ADVISOR']
        ).order_by('-created_at').first()

        if open_question:
            keyboard = [
                [InlineKeyboardButton("Да", callback_data='close_question_yes')],
                [InlineKeyboardButton("Нет", callback_data='close_question_no')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Удовлетворены ли вы ответом?', reply_markup=reply_markup)
        else:
            update.message.reply_text('У вас нет активных вопросов для закрытия.')
    else:
        update.message.reply_text('Пожалуйста, сначала пройдите аутентификацию.')

def handle_close_response(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    student = context.user_data.get('student')

    if student:
        open_question = Question.objects.filter(
            student=student,
            status__in=['NEW', 'IN_PROCESS', 'MAIN_ADVISOR']
        ).order_by('-created_at').first()

        if open_question:
            if data == 'close_yes':
                open_question.status = 'CLOSED'  # Примерный статус "Закрыт"
                open_question.save()
                query.edit_message_text(text="Ваш вопрос успешно закрыт. Спасибо за обращение.")
            elif data == 'close_no':
                # Назначаем вопрос главному эдвайзеру
                main_advisor = User.objects.filter(groups__name='Main Advisor').first()
                if main_advisor:
                    open_question.assigned_user = main_advisor
                    open_question.status = 'MAIN_ADVISOR'  # Примерный статус "На рассмотрении у главного эдвайзера"
                    open_question.save()
                    query.edit_message_text(text="Ваш вопрос передан главному эдвайзеру для дальнейшего рассмотрения.")
                else:
                    query.edit_message_text(text="Ошибка: главный эдвайзер не найден.")
        else:
            query.edit_message_text(text='У вас нет активных вопросов для закрытия.')
    else:
        query.edit_message_text(text='Ошибка обработки запроса.')


# АВТОРИЗАЦИЯ ДЛЯ ПРЕПОДОВ
def button_teach(update, context):
    query = update.callback_query
    query.answer()

    if query.data == 'teacher':
        context.user_data['role'] = 'teacher'
        context.bot.send_message(chat_id=update.effective_chat.id, text="Преподаватель или сотрудник?\n\nПожалуйста, войдите здесь. Для отмены авторизации или смены роли нажмите\n/cancel")
        context.bot.send_message(chat_id=update.effective_chat.id, text="Введите ваш логин :")
        return USERNAME_TEACH
    
USERNAME_TEACH, PASSWORD_TEACH = range(2)

def receive_username_teach(update, context):
    username = update.message.text
    if "@almau.edu.kz" not in username:
        username += "@almau.edu.kz"
    context.user_data['auth_username'] = username
    update.message.reply_text("Введите ваш пароль:")
    return PASSWORD_TEACH

def receive_password_teach(update, context):
    username = context.user_data.get('auth_username')
    password = update.message.text

    if check_ad_credentials_teach(AD_SERVER, username, password):
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save()
            lecturer, lecturer_created = Lecturer.objects.get_or_create(
                user=user,
                defaults={'username': username, 'chat_id': update.message.chat_id}
            )
            if lecturer_created:
                update.message.reply_text("Вы зарегистрированы как преподаватель.")
            else:
                lecturer.chat_id = update.message.chat_id
                lecturer.save()
                update.message.reply_text("Вы уже зарегистрированы как преподаватель.")
        else:
            lecturer, lecturer_created = Lecturer.objects.get_or_create(
                user=user,
                defaults={'username': username, 'chat_id': update.message.chat_id}
            )
            if not lecturer_created:
                lecturer.chat_id = update.message.chat_id
                lecturer.save()

        context.user_data['user'] = user
        start(update, context)
        return ConversationHandler.END
    else:
        update.message.reply_text('Неверные учетные данные.')
        context.user_data.clear()
        start(update, context)
        return ConversationHandler.END

DESCRIPTION, AUDITORIUM = range(2)

def start_request(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text('Опишите проблему:')
    return DESCRIPTION

def receive_description(update, context):
    context.user_data['description'] = update.message.text
    update.message.reply_text('Введите номер аудитории:')
    return AUDITORIUM

def receive_auditorium(update, context):
    user = context.user_data.get('user')
    description = context.user_data.get('description')
    auditorium_number = update.message.text
    new_request = HelpDeskRequest.objects.create(auditorium_number=auditorium_number, description=description, creator=user)
    update.message.reply_text('Ваша заявка создана. Ожидайте специалиста')
    notify_helpdesk_about_new_request(new_request, context.bot)
    return ConversationHandler.END

def notify_helpdesk_about_new_request(request, bot):
    helpdesk_users = HelpDeskUser.objects.all()
    message_text = f"Новая заявка: ❗\nАудитория: {request.auditorium_number}\nПроблема: {request.description}\nОт: {request.creator}"

    for helpdesk_user in helpdesk_users:
        if helpdesk_user.chat_id:  # Добавляем проверку на наличие chat_id
            keyboard = [
                [InlineKeyboardButton("Принять", callback_data=f"accept_{request.id}")],
                [InlineKeyboardButton("Отклонить", callback_data=f"decline_{request.id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(chat_id=helpdesk_user.chat_id, text=message_text, reply_markup=reply_markup)
        else:
            print(f"Ошибка: у HelpDeskUser {helpdesk_user.user.username} отсутствует chat_id.")

def accept_request(update, context):
    query = update.callback_query
    request_id = query.data.split('_')[1]
    request = HelpDeskRequest.objects.get(id=request_id)
    
    if request.status == HelpDeskRequest.IN_PROCESS:
        query.edit_message_text(text=f"Заявка {request_id} уже в обработке.")
        return
    
    if request.status == HelpDeskRequest.NEW:
        helpdesk_user = HelpDeskUser.objects.get(chat_id=query.message.chat_id)
        
        if hasattr(helpdesk_user, 'user'):
            request.handler = helpdesk_user.user
            request.status = HelpDeskRequest.IN_PROCESS
            request.save()
            query.edit_message_text(text=f"Заявка {request_id} принята в обработку.")
            
            # Используем модель Lecturer для получения chat_id создателя заявки
            try:
                lecturer = Lecturer.objects.get(user=request.creator)
                if lecturer.chat_id:
                    context.bot.send_message(chat_id=lecturer.chat_id, text=f"Ваша заявка принята в обработку.")
                else:
                    print("Ошибка: у создателя заявки нет chat_id.")
            except Lecturer.DoesNotExist:
                print("Ошибка: создатель заявки не зарегистрирован как преподаватель.")
        else:
            query.edit_message_text(text="Ошибка: сотрудник HelpDesk не найден.")
    else:
        query.edit_message_text(text="Заявка уже не новая и не может быть принята.")

(SELECT_REASON, CUSTOM_REASON) = range(2)

def start_decline(update, context):
    query = update.callback_query
    request_id = query.data.split('_')[1]
    context.user_data['decline_request_id'] = request_id

    keyboard = [
        [InlineKeyboardButton("Нет полной информации", callback_data='decline_reason_info')],
        [InlineKeyboardButton("Некорректно оформленная заявка", callback_data='decline_reason_format')],
        [InlineKeyboardButton("Данная заявка оформляется через документолог", callback_data='decline_reason_doc')],
        [InlineKeyboardButton("Своя причина", callback_data='decline_reason_custom')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text('Выберите причину отклонения заявки:', reply_markup=reply_markup)

    return SELECT_REASON

def select_reason(update, context):
    query = update.callback_query
    reason_key = query.data.split('_')[2]

    if reason_key == 'custom':
        query.edit_message_text('Введите свою причину отклонения заявки:')
        return CUSTOM_REASON
    else:
        reasons = {
            'info': "Нет полной информации",
            'format': "Некорректно оформленная заявка",
            'doc': "Данная заявка оформляется через документолог"
        }
        reason = reasons[reason_key]
        handle_decline(update, context, reason)
        return ConversationHandler.END
    
def custom_reason(update, context):
    custom_reason = update.message.text
    handle_decline(update, context, custom_reason)
    return ConversationHandler.END

def handle_decline(update, context, reason):
    request_id = context.user_data['decline_request_id']
    request = HelpDeskRequest.objects.get(id=request_id)

    # Устанавливаем статус заявки и сохраняем причину отказа
    request.status = HelpDeskRequest.CLOSED
    request.is_closed = True
    request.decline_reason = reason

    helpdesk_user = HelpDeskUser.objects.get(user=context.user_data['user'])
    request.handler = helpdesk_user.user
    request.save()

    # Отправляем сообщение пользователю о том, что заявка отклонена
    if update.callback_query:
        update.callback_query.message.reply_text(f"Заявка {request_id} отклонена по следующей причине: {reason}")
    else:
        # Если обновление инициировано не через CallbackQuery, используем update.message
        if update.message:
            update.message.reply_text(f"Заявка {request_id} отклонена по следующей причине: {reason}")

    # Отправляем уведомление создателю заявки
    try:
        lecturer = Lecturer.objects.get(user=request.creator)
        if lecturer.chat_id:
            context.bot.send_message(chat_id=lecturer.chat_id, text=f"Ваша заявка была отклонена по следующей причине: {reason}")
        else:
            print("Ошибка: у создателя заявки нет chat_id.")
    except Lecturer.DoesNotExist:
        print("Ошибка: создатель заявки не зарегистрирован как преподаватель.")
# def decline_request(update, context):
#     query = update.callback_query
#     request_id = query.data.split('_')[1]
#     request = HelpDeskRequest.objects.get(id=request_id)

#     if request.status in [HelpDeskRequest.IN_PROCESS, HelpDeskRequest.CLOSED]:
#         query.edit_message_text(text=f"Заявка {request_id} уже в обработке или закрыта и не может быть отклонена.")
#         return

#     helpdesk_user = HelpDeskUser.objects.get(chat_id=query.message.chat_id)
    
#     if hasattr(helpdesk_user, 'user'):
#         request.status = HelpDeskRequest.CLOSED
#         request.is_closed = True
#         request.handler = helpdesk_user.user
#         request.save()
#         query.edit_message_text(text=f"Заявка {request_id} отклонена.")
        
#         # Получаем объект Lecturer для создателя заявки
#         try:
#             lecturer = Lecturer.objects.get(user=request.creator)
#             if lecturer.chat_id:
#                 context.bot.send_message(chat_id=lecturer.chat_id, text=f"Ваша заявка отклонена.")
#             else:
#                 print("Ошибка: у создателя заявки нет chat_id.")
#         except Lecturer.DoesNotExist:
#             print("Ошибка: создатель заявки не зарегистрирован как преподаватель.")
#     else:
#         query.edit_message_text(text="Ошибка: сотрудник HelpDesk не найден.")

def view_requests_handler(update, context):
    query = update.callback_query
    query.answer()

    requests = HelpDeskRequest.objects.filter(status=HelpDeskRequest.NEW)

    if not requests.exists():
        query.edit_message_text('На данный момент новых заявок нет.\n/start - главное меню.')
        return

    for request in requests:
        formatted_date = request.created_at.strftime('%H:%M %d.%m.%Y')
        message_text = (f"🚩 Заявка #{request.id} от {formatted_date}\n"
                        f"Преподаватель: {request.creator}\n"
                        f"Ответственный: {request.handler}\n"
                        f"Проблема: {request.description}\n"
                        f"Аудитория: {request.auditorium_number}\n"
                        f"Статус: {request.get_status_display()}")

        keyboard = [
            [InlineKeyboardButton("Принять", callback_data=f"accept_{request.id}")],
            [InlineKeyboardButton("Отклонить", callback_data=f"decline_{request.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=query.message.chat_id, text=message_text, reply_markup=reply_markup)

    query.delete_message()

def view_my_requests_handler(update, context):
    query = update.callback_query
    query.answer()

    current_user = context.user_data.get('user')
    my_requests = HelpDeskRequest.objects.filter(handler=current_user, status=HelpDeskRequest.IN_PROCESS)

    if not my_requests.exists():
        query.edit_message_text('У вас нет активных заявок. /start - главное меню.')
        return

    message_text = "Список моих заявок:\n\n"
    for request in my_requests:
        formatted_date = request.created_at.strftime('%H:%M %d.%m.%Y')
        message_text += (f"🚩 Заявка #{request.id} от {formatted_date}\n"
                         f"Преподаватель: {request.creator}\n"
                         f"Ответсвенный: {request.handler}\n"
                         f"Проблема: {request.description}\n"
                         f"Аудитория: {request.auditorium_number}\n"
                        f"Статус: {request.get_status_display()}")
        
        keyboard = [[InlineKeyboardButton("Закрыть", callback_data=f"close_request_{request.id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(chat_id=query.message.chat_id, text=message_text, reply_markup=reply_markup)

    query.delete_message()

def close_request_handler(update, context):
    query = update.callback_query
    _, action, request_id = query.data.split('_')
    try:
        request = HelpDeskRequest.objects.get(id=request_id)
        request.status = HelpDeskRequest.CLOSED
        request.is_closed = True
        request.save()
        query.edit_message_text(f"Заявка #{request_id} успешно закрыта.")
        start(update, context)
    except HelpDeskRequest.DoesNotExist:
        query.edit_message_text(f"Ошибка: заявка с ID {request_id} не найдена.")

def view_closed_requests_handler(update, context):
    query = update.callback_query
    query.answer()

    closed_requests = HelpDeskRequest.objects.filter(status=HelpDeskRequest.CLOSED).order_by('-created_at')[:5]

    if not closed_requests.exists():
        query.edit_message_text('На данный момент закрытых заявок нет.')
        start(update, context)
        return

    message_text = "Список последних 5 закрытых заявок:\n\n"
    for request in closed_requests:
        formatted_date = request.created_at.strftime('%H:%M %d.%m.%Y')
        message_text += (f"🚩 Заявка #{request.id} от {formatted_date}\n"
                         f"Преподаватель: {request.creator}\n"
                         f"Ответсвенный: {request.handler}\n"
                         f"Проблема: {request.description}\n"
                         f"Аудитория: {request.auditorium_number}\n"
                         f"Статус: Закрыта\n\n")

    query.edit_message_text(message_text)

def logout(update, context):
    # Очищаем данные пользователя
    context.user_data.clear()

    # Проверяем, есть ли данные CallbackQuery
    if update.callback_query:
        # Здесь вы можете обработать данные CallbackQuery или сбросить их
        update.callback_query.answer()  # Например, отправляем пустой ответ на CallbackQuery
        update.callback_query.edit_message_text('Вы вышли из системы.')  # Редактируем сообщение, чтобы убрать клавиатуру
    else:
        # Если это обычное текстовое сообщение
        update.message.reply_text('Вы вышли из системы.')

    return ConversationHandler.END

def main():
    from telegram.utils.request import Request
    request = Request(con_pool_size=8, urllib3_proxy_kwargs={'verify': False})
    bot = Bot('6381298802:AAFmZVISMBO9k9_T8MwweqBZFXoFuIGgOCg', request=request)
    updater = Updater(bot=bot, use_context=True)
    dp = updater.dispatcher

    # СТАРТ
    dp.add_handler(CommandHandler('start', start))

    # АВТОРИЗАЦИЯ ДЛЯ СТУДЕНТОВ
    auth_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='student')],
        states={
            USERNAME: [MessageHandler(Filters.text & ~Filters.command, receive_username)],
            PASSWORD: [MessageHandler(Filters.text & ~Filters.command, receive_password)],
            FULL_NAME: [MessageHandler(Filters.text & ~Filters.command, receive_full_name)],
            COURSE: [MessageHandler(Filters.text & ~Filters.command, receive_course)],
            SPECIALTY: [MessageHandler(Filters.text & ~Filters.command, receive_specialty)],
            GENDER: [MessageHandler(Filters.regex('^(Мужской|Женский)$'), receive_gender)],
            DEPARTMENT: [MessageHandler(Filters.regex('^(Казахский|Русский|Английский)$'), receive_department)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)]
    )

    dp.add_handler(auth_handler)

    # ПЕРЕПИСКА
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_question, pattern='ask_adviser')],
        states={
            TYPING_QUESTION: [
                MessageHandler(Filters.text & ~Filters.command, handle_question_text),
                MessageHandler(~Filters.text, handle_non_text_message)  # Добавляем этот обработчик
            ],
        },
        fallbacks=[CommandHandler('logout', logout), CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
    faq_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(faq_command, pattern='faq')],
        states={
            FAQ_QUESTION: [MessageHandler(Filters.text & ~Filters.command, handle_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Добавление обработчика диалога в диспетчер
    dp.add_handler(faq_handler)

    # Обработчик для кнопки "Вопрос эдвайзеру"
    dp.add_handler(CallbackQueryHandler(ask_question, pattern='ask_adviser'))

    # Обработчик для закрытия чата
    dp.add_handler(CallbackQueryHandler(handle_close_response, pattern='^close_question_'))
    dp.add_handler(CallbackQueryHandler(close_chat, pattern='^close_question_yes$'))
    dp.add_handler(CallbackQueryHandler(close_chat, pattern='^close_question_no$'))

    # АВТОРИЗАЦИЯ ДЛЯ ПРЕПОДОВ
    auth_handler_teach = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_teach, pattern='teacher')],
        states={
            USERNAME_TEACH: [MessageHandler(Filters.text & ~Filters.command, receive_username_teach)],
            PASSWORD_TEACH: [MessageHandler(Filters.text & ~Filters.command, receive_password_teach)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)]
    )

    dp.add_handler(auth_handler_teach)

    # ВЫХОД
    logout_handler = CommandHandler('logout', logout)
    dp.add_handler(logout_handler)

    # CОЗДАНИЕ ЗАЯВКИ
    request_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_request, pattern='^create_request$')],
        states={
            DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, receive_description)],
            AUDITORIUM: [MessageHandler(Filters.text & ~Filters.command, receive_auditorium)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)]
    )
    dp.add_handler(request_conv_handler)

    dp.add_handler(CallbackQueryHandler(view_requests_handler, pattern='^show_request$'))
    dp.add_handler(CallbackQueryHandler(view_my_requests_handler, pattern='^show_my_requests$'))
    dp.add_handler(CallbackQueryHandler(view_closed_requests_handler, pattern='^show_closed_requests$'))

    #ОБРАБОТЧИКИ HELPDESK
    dp.add_handler(CallbackQueryHandler(accept_request, pattern='^accept_'))
    decline_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_decline, pattern='^decline_')],
        states={
            SELECT_REASON: [CallbackQueryHandler(select_reason, pattern='^decline_reason_')],
            CUSTOM_REASON: [MessageHandler(Filters.text & ~Filters.command, custom_reason)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(decline_handler)
    dp.add_handler(CallbackQueryHandler(close_request_handler, pattern='^close_request_'))

    print("Starting bot...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()