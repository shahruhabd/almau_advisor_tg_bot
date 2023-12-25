# import os
# import django

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Almau_Advisor.settings")
# django.setup()

# import datetime
# from Advisor.models import FAQ, Student, Specialty, Question
# from django.contrib.auth.models import User, Group
# from django.db.models import Count
# from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
# from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, Filters
# import ldap3



# # Статусы для состояний диалога
# WAITING_FOR_USERNAME, WAITING_FOR_PASSWORD, WAITING_FOR_FULL_NAME, WAITING_FOR_COURSE, WAITING_FOR_SPECIALTY, WAITING_FOR_GENDER, WAITING_FOR_DEPARTMENT, WAITING_FOR_QUESTION = range(8)

# def start_student(update, context):
#     keyboard = [
#         [InlineKeyboardButton("Часто задаваемые вопросы", callback_data='faq')],
#         [InlineKeyboardButton("Задать свой вопрос", callback_data='ask')]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     update.callback_query.message.reply_text('Выберите опцию:', reply_markup=reply_markup)

# def faq_command(update, context):
#     faqs = FAQ.objects.all()
#     response = ''
#     for i, faq in enumerate(faqs):
#         response += f"{i+1}. {faq.question}\n{faq.answer}\n\n"
#     update.message.reply_text(response)

# def ask_command(update, context):
#     update.message.reply_text('Введите ваш логин.')
#     return WAITING_FOR_USERNAME
    

# def auth_and_ask_question(update, context):
#     if update.message.text == '📚 Часто задаваемые вопросы':
#         faq_command(update, context)
#     elif update.message.text == '❓ Задать свой вопрос':
#         ask_command(update, context)
#     else:
#         chat_id = update.message.chat_id
#         current_state = context.user_data.get('state', None)

#         if current_state == 'waiting_for_username':
#             current_time = datetime.datetime.now().time()

#             start_time = datetime.time(9, 0)
#             end_time = datetime.time(19, 0)
#             if start_time <= current_time <= end_time:
#                 username = update.message.text
#                 if "@almau.edu.kz" not in username:
#                     username += "@almau.edu.kz"
#                 context.user_data['username'] = username
#                 update.message.reply_text('Введите ваш пароль.')
#                 context.user_data['state'] = 'waiting_for_password'
#             else:
#                 update.message.reply_text("Бот работает с 9:00 до 18:00. Пожалуйста, обратитесь в рабочее время.") 

#         elif current_state == 'waiting_for_password':
#             password = update.message.text
#             username = context.user_data['username']

#             if check_ad_credentials(AD_SERVER, username, password):
#                 student, created = Student.objects.get_or_create(username=username, defaults={'chat_id': chat_id})

#                 if created or not (student.full_name and student.course and student.specialty):
#                     context.user_data['state'] = 'waiting_for_full_name'
#                     context.user_data['student'] = student
#                     update.message.reply_text('Аутентификация успешна. Введите ваше полное ФИО.')
#                 else:
#                     context.user_data['student'] = student
#                     context.user_data['state'] = 'authenticated'
#                     update.message.reply_text('Спасибо, ваш профиль уже заполнен. Теперь вы можете задать свой вопрос.')
                    
#                 print(f"пользователь {student} авторизировался")
#             else:
#                 update.message.reply_text('Неверные учетные данные.')

#         elif current_state == 'waiting_for_full_name':
#             full_name = update.message.text
#             update.message.reply_text('Введите ваш курс (от 1 до 4).')
#             context.user_data['full_name'] = full_name
#             context.user_data['state'] = 'waiting_for_course'

#         elif current_state == 'waiting_for_course':
#             course = update.message.text
#             update.message.reply_text('Выберите вашу специальность из списка ниже. \n(просто отправьте цифру, например 1)')
#             specialties = Specialty.objects.all()
#             for idx, specialty in enumerate(specialties):
#                 update.message.reply_text(f'{idx + 1}. {specialty.name}')
#             context.user_data['course'] = course
#             context.user_data['state'] = 'waiting_for_specialty'

#         elif current_state == 'waiting_for_specialty':
#             selected_idx = int(update.message.text) - 1
#             specialties = Specialty.objects.all()
#             if 0 <= selected_idx < len(specialties):
#                 selected_specialty = specialties[selected_idx]
#                 context.user_data['selected_specialty'] = selected_specialty.id
#                 context.user_data['details_filled'] = True
#                 context.user_data['state'] = 'waiting_for_gender'  # Измените состояние на ожидание ввода пола

#                 ask_gender(update, context)  # Вызовите функцию для отображения кнопок выбора пола

#             else:
#                 update.message.reply_text('Некорректный выбор. Попробуйте еще раз.')   
#         else: 
#             ask_question(update, context)

# def ask_gender(update, context):
#     keyboard = [
#         [InlineKeyboardButton("Мужской", callback_data='M')],
#         [InlineKeyboardButton("Женский", callback_data='F')]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     update.message.reply_text('Выберите ваш пол:', reply_markup=reply_markup)
#     context.user_data['state'] = 'waiting_for_gender'

# def ask_department(update, context):
#     query = update.callback_query 
#     keyboard = [
#         [InlineKeyboardButton("Казахское", callback_data='KZ')],
#         [InlineKeyboardButton("Русское", callback_data='RU')],
#         [InlineKeyboardButton("Английское", callback_data='EN')]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     query.message.reply_text('Выберите ваше отделение:', reply_markup=reply_markup)
#     context.user_data['state'] = 'waiting_for_department'


# def ask_question(update, context):
#     student = context.user_data.get('student')

#     if student:
#         # Получаем последний вопрос пользователя, который не закрыт
#         question = Question.objects.filter(
#             student=student, 
#             status__in=['NEW', 'MAIN_ADVISOR', 'IN_PROCESS']
#         ).last()

#         # Если открытый вопрос уже существует, добавляем к нему сообщение
#         if question:
#             current_time = datetime.timezone.now().strftime('%H:%M')
#             new_entry = {'type': 'question', 'text': update.message.text, 'timestamp': current_time}
#             if question.conversation:
#                 question.conversation.append(new_entry)
#             else:
#                 question.conversation = [new_entry]
#             question.save()
#             text_to_send = 'Ваше сообщение добавлено к текущему вопросу.'
#         else:
#             # Если открытых вопросов нет, создаем новый
#             assigned_user = User.objects.filter(groups__name='Advisor').annotate(num_requests=Count('assigned_requests')).order_by('num_requests').first()
#             new_question = Question.objects.create(
#                 student=student, 
#                 status='NEW',  # Установка начального статуса нового вопроса
#                 conversation=[{
#                     'type': 'question',
#                     'text': update.message.text,
#                     'timestamp': datetime.timezone.now().strftime('%H:%M')
#                 }],
#                 assigned_user=assigned_user
#             )
#             text_to_send = 'Ваш вопрос зарегистрирован. Мы постараемся ответить как можно скорее.'

#         update.message.reply_text(text_to_send)
#     else:
#         update.message.reply_text('Пожалуйста, сначала пройдите аутентификацию.')

# def close_chat(update, context):
#     keyboard = [
#         [InlineKeyboardButton("Да", callback_data='yes'),
#          InlineKeyboardButton("Нет", callback_data='no')]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     update.message.reply_text('Удовлетворены ли вы ответом?', reply_markup=reply_markup)

# def button(update, context):
#     # query = update.callback_query
#     # data = query.data
#     # student_username = context.user_data.get('username')

#     query = update.callback_query
#     query.answer()
#     data = query.data
#     if data == 'student':
#         student_keyboard(update, context)
#     # Проверяем, ожидаем ли мы выбор пола или отделения
#         if context.user_data.get('state') == 'waiting_for_gender':
#             context.user_data['gender'] = data
#             context.user_data['state'] = 'waiting_for_department'
#             ask_department(update, context)
#             query.answer()
#             return

#         elif context.user_data.get('state') == 'waiting_for_department':
#             context.user_data['department'] = data
#             student_username = context.user_data.get('username')
#             if student_username:
#                 save_student_profile(student_username, context.user_data)
#             # Переход к следующему шагу
#             context.user_data['state'] = 'waiting_for_question'
#             query.message.reply_text('Теперь вы можете задать свой вопрос.')
#             query.answer()
#             return
        
#         student = context.user_data.get('student', None)
#         # Если мы не ожидаем выбора пола или отделения, значит это закрытие вопроса
#         if student and data in ['yes', 'no']:
#             open_question = Question.objects.filter(
#                 student=student,
#                 status__in=['NEW', 'IN_PROCESS', 'MAIN_ADVISOR']
#             ).order_by('-created_at').first()

#             if open_question:
#                 if data == 'yes':
#                     open_question.status = 'CLOSED'
#                     open_question.save()
#                     query.edit_message_text(text="Спасибо за вашу оценку. Чат закрыт.")
#                 elif data == 'no':
#                     main_advisor_group = Group.objects.get(name='Main Advisor')
#                     main_advisor_users = main_advisor_group.user_set.all()
#                     assigned_user = main_advisor_users.first()
#                     open_question.assigned_user = assigned_user
#                     open_question.status = 'MAIN_ADVISOR'
#                     open_question.save()
#                     query.edit_message_text(text="Ваш запрос будет рассмотрен главой ЭЦ.")
#             else:
#                 update.callback_query.message.reply_text('Нет активного вопроса для закрытия.')

# def save_student_profile(student_username, user_data):
#     try:
#         # Используем get() для извлечения объекта, так как get_or_create() уже был вызван ранее в коде
#         student = Student.objects.get(username=student_username)
#         student.full_name = user_data.get('full_name', student.full_name)
#         student.gender = user_data.get('gender', student.gender)
#         student.department = user_data.get('department', student.department)
#         student.course = user_data.get('course', student.course)
        
#         # Проверяем, есть ли в user_data выбранная специальность, и обновляем её у студента
#         if 'selected_specialty' in user_data:
#             specialty_id = user_data['selected_specialty']
#             student.specialty_id = specialty_id
        
#         student.save()
#         print(f"Student {student.username} profile updated with full_name {student.full_name}")
#     except Student.DoesNotExist:
#         print(f"Student with username {student_username} does not exist.")


# def check_ad_credentials(ad_server, username, password):
#     with ldap3.Connection(ad_server, user=username, password=password, auto_bind=True) as conn:
#         if not conn.bind():
#             print('Error in bind:', conn.result)  # для отладки
#             return False

#         username = username.split('@')[0]

#         # Поиск в корневом DN для всех пользователей, кроме тех, кто находится в OU=UsersDoc
#         base_dn = 'OU=STUDENTS,DC=iab,DC=kz'
#         # search_filter = f'(&(objectClass=user)(sAMAccountName={username})(!(distinguishedName=*OU=UsersDoc,*)))'
#         search_filter = f'(&(objectClass=user)(sAMAccountName={username}))'

#         conn.search(base_dn, search_filter, attributes=['memberOf'])

#         if len(conn.entries) != 1:
#             return False

#         # Пользователь найден и он не находится в OU=UsersDoc
#         return True
    

# student_conv_handler = ConversationHandler(
#     entry_points=[CallbackQueryHandler(start_student, pattern='^student$')],
#     states={
#         WAITING_FOR_USERNAME: [MessageHandler(Filters.text, auth_and_ask_question)],
#         WAITING_FOR_PASSWORD: [MessageHandler(Filters.text, auth_and_ask_question)],
#         WAITING_FOR_FULL_NAME: [MessageHandler(Filters.text, auth_and_ask_question)],
#         WAITING_FOR_COURSE: [MessageHandler(Filters.text, auth_and_ask_question)],
#         WAITING_FOR_SPECIALTY: [MessageHandler(Filters.text, auth_and_ask_question)],
#         WAITING_FOR_GENDER: [CallbackQueryHandler(ask_gender)],
#         WAITING_FOR_DEPARTMENT: [CallbackQueryHandler(ask_department)],
#         WAITING_FOR_QUESTION: [MessageHandler(Filters.text, ask_question)]
#     },
#     fallbacks=[CommandHandler('cancel', close_chat)]
# )