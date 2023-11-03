import datetime
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Almau_Advisor.settings")
django.setup()

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from django.core.exceptions import ObjectDoesNotExist
from Advisor.models import Student, Question, Specialty, FAQ
from django.contrib.auth.models import User, Group
from django.db.models import Count
from django.conf import settings
import ldap3
from ldap3 import Server, Connection
from django.utils import timezone

AD_SERVER = 'ldap://dca.iab.kz'

def start(update, context):
    keyboard = [
        ["📚 Часто задаваемые вопросы"],
        ["❓ Задать свой вопрос"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text('Приветсвуем! Чем могу помочь?', reply_markup=reply_markup)

def faq_command(update, context):
    faqs = FAQ.objects.all()
    response = ''
    for i, faq in enumerate(faqs):
        response += f"{i+1}. {faq.question}\n{faq.answer}\n\n"
    update.message.reply_text(response)

def ask_command(update, context):
    update.message.reply_text('Введите ваш логин.')
    context.user_data['state'] = 'waiting_for_username'
    

def auth_and_ask_question(update, context):
    if update.message.text == '📚 Часто задаваемые вопросы':
        faq_command(update, context)
    elif update.message.text == '❓ Задать свой вопрос':
        ask_command(update, context)
    else:
        chat_id = update.message.chat_id
        current_state = context.user_data.get('state', None)

        if current_state == 'waiting_for_username':
            current_time = datetime.datetime.now().time()

            start_time = datetime.time(9, 0)
            end_time = datetime.time(18, 0)
            if start_time <= current_time <= end_time:
                username = update.message.text
                if "@almau.edu.kz" not in username:
                    username += "@almau.edu.kz"
                context.user_data['username'] = username
                update.message.reply_text('Введите ваш пароль.')
                context.user_data['state'] = 'waiting_for_password'
            else:
                update.message.reply_text("Бот работает с 9:00 до 18:00. Пожалуйста, обратитесь в рабочее время.") 

        elif current_state == 'waiting_for_password':
            password = update.message.text
            username = context.user_data['username']

            if check_ad_credentials(AD_SERVER, username, password):
                student, created = Student.objects.get_or_create(username=username, defaults={'chat_id': chat_id})

                if created or not (student.full_name and student.course and student.specialty):
                    context.user_data['state'] = 'waiting_for_full_name'
                    context.user_data['student'] = student
                    update.message.reply_text('Аутентификация успешна. Введите ваше полное ФИО.')
                else:
                    context.user_data['student'] = student
                    context.user_data['state'] = 'authenticated'
                    update.message.reply_text('Спасибо, ваш профиль уже заполнен. Теперь вы можете задать свой вопрос.')
                    
                print(f"пользователь {student} авторизировался")
            else:
                update.message.reply_text('Неверные учетные данные.')

        elif current_state == 'waiting_for_full_name':
            full_name = update.message.text
            update.message.reply_text('Введите ваш курс (от 1 до 4).')
            context.user_data['full_name'] = full_name
            context.user_data['state'] = 'waiting_for_course'

        elif current_state == 'waiting_for_course':
            course = update.message.text
            update.message.reply_text('Выберите вашу специальность из списка ниже.')
            specialties = Specialty.objects.all()
            for idx, specialty in enumerate(specialties):
                update.message.reply_text(f'{idx + 1}. {specialty.name}')
            context.user_data['course'] = course
            context.user_data['state'] = 'waiting_for_specialty'

        elif current_state == 'waiting_for_specialty':
            selected_idx = int(update.message.text) - 1
            specialties = Specialty.objects.all()
            if 0 <= selected_idx < len(specialties):
                selected_specialty = specialties[selected_idx]
                context.user_data['specialty'] = selected_specialty
                context.user_data['details_filled'] = True
                context.user_data['state'] = 'authenticated'
                
                # Здесь сохраняем все собранные данные в модель Student
                student = context.user_data['student']
                student.full_name = context.user_data['full_name']
                student.course = context.user_data['course']
                student.specialty = selected_specialty
                student.save()
                
                update.message.reply_text('Спасибо, ваш профиль обновлен. Теперь вы можете задать свой вопрос в текстовом поле ')
            else:
                update.message.reply_text('Некорректный выбор. Попробуйте еще раз.')
        else: 
            ask_question(update, context)


def ask_question(update, context):
    student = context.user_data.get('student')

    if student:
        previous_question = Question.objects.filter(student=student).last()
        advisor_group = Group.objects.get(name='Advisor')
        advisor_users = advisor_group.user_set.annotate(num_requests=Count('assigned_requests')).order_by('num_requests')
        assigned_user = advisor_users.first()
        new_question, created = Question.objects.get_or_create(
            student=student, 
            is_closed=False, 
            defaults={
                'conversation': [],
                'assigned_user': assigned_user
            }
        )

        if previous_question and previous_question.is_closed:
            text_to_send = 'Ваша предыдущая заявка закрыта. Создана новая заявка. Мы постараемся ответить как можно скорее.'
        else:
            text_to_send = 'Ваш вопрос создан. Мы постараемся ответить как можно скорее.'

        if new_question.conversation is None:
            new_question.conversation = []

        current_time = timezone.now().strftime('%H:%M')
        new_entry = {'type': 'question', 'text': update.message.text, 'timestamp': current_time}
        new_question.conversation.append(new_entry)
        new_question.save()

        update.message.reply_text(text_to_send)
    else:
        update.message.reply_text('Пожалуйста, сначала пройдите аутентификацию.')

def close_chat(update, context):
    keyboard = [
        [InlineKeyboardButton("Да", callback_data='yes'),
         InlineKeyboardButton("Нет", callback_data='no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Удовлетворены ли вы ответом?', reply_markup=reply_markup)

def button(update, context):
    student = context.user_data.get('student')
    if student:
        try:
            question = Question.objects.get(student=student)
            query = update.callback_query
            if query.data == 'yes':
                question.status = 'CLOSED'
                question.save()
                query.edit_message_text(text="Спасибо за вашу оценку. Чат закрыт.")
            elif query.data == 'no':
                main_advisor_group = Group.objects.get(name='Main Advisor')
                main_advisor_users = main_advisor_group.user_set.all()
                assigned_user = main_advisor_users.first()
                question.assigned_user = assigned_user
                question.status = 'MAIN_ADVISOR'
                question.save()
                query.edit_message_text(text="Ваш запрос будет рассмотрен главой ЭЦ.")
        except Question.DoesNotExist:
            update.message.reply_text('Нет активного чата для закрытия.')

def check_ad_credentials(ad_server, username, password):
    with ldap3.Connection(ad_server, user=username, password=password) as conn:
        return conn.bind()

updater = Updater(token=settings.TELEGRAM_BOT_TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CallbackQueryHandler(button))
dp.add_handler(CommandHandler('start', start))
dp.add_handler(CommandHandler('faq', faq_command))  # Новый обработчик для /faq
dp.add_handler(CommandHandler('ask', ask_command))
dp.add_handler(CommandHandler('close', close_chat))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, auth_and_ask_question))

updater.start_polling()
updater.idle()