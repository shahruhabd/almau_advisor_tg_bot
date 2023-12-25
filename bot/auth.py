# from telegram.ext import ConversationHandler
# from django.contrib.auth.models import User
# from helpdesk.models import Lecturer, HelpDeskUser
# from Advisor.models import Student
# from telegram import InlineKeyboardButton, InlineKeyboardMarkup
# from bot.teachers import create_request

# import ldap3

# AD_SERVER = 'ldap://dca.iab.kz'

# def check_ad_credentials(AD_SERVER, username, password):
#     with ldap3.Connection(AD_SERVER, user=username, password=password) as conn:
#         return conn.bind()

# def start_authentication(update, context):
#     if 'authenticated' in context.user_data:
#             update.message.reply_text(f'Вы уже авторизованы\nЕсли желаете выйти /logout')
#     else:
#         update.message.reply_text('Пожалуйста, введите ваш логин:')
#         return "AWAITING_USERNAME"

# def receive_username(update, context):
#     username = update.message.text
#     if "@almau.edu.kz" not in username:
#         username += "@almau.edu.kz"
#     context.user_data['auth_username'] = username
#     update.message.reply_text("Пожалуйста, введите ваш пароль.")
#     return "AWAITING_PASSWORD"

# def receive_password(update, context):
#     username = context.user_data.get('auth_username')
#     password = update.message.text

#     if check_ad_credentials(AD_SERVER, username, password):
#         user, created = User.objects.get_or_create(username=username)
#         if created:
#             user.set_password(password)
#             user.save()

#         context.user_data['username'] = username
#         update.message.reply_text("Вы успешно аутентифицированы.")
#         context.user_data['authenticated'] = True
#         context.user_data['user'] = user
#         user_role_choice(update, context)
#     else:
#         update.message.reply_text("Неправильный логин или пароль.")
#     return ConversationHandler.END

# def user_role_choice(update, context):
#     keyboard = [
#         [InlineKeyboardButton("Студент", callback_data='student')],
#         [InlineKeyboardButton("HelpDesk", callback_data='helpdesk')],
#         [InlineKeyboardButton("Преподаватель", callback_data='lecturer')]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     update.message.reply_text('Кто вы?', reply_markup=reply_markup)


# def logout(update, context):
#     context.user_data.clear()  # Удаляет все данные пользователя
#     update.message.reply_text('Вы вышли из системы.')
#     return ConversationHandler.END

# def handle_lecturer(update, context):
#     user = context.user_data.get('user')
#     if user is not None:
#         created, lecturer = Lecturer.objects.get_or_create(username=user.username, defaults={'chat_id': update.effective_chat.id})
#         if created or update.callback_query:
#             # Создаем клавиатуру с кнопкой "Вызвать IT-специалиста"
#             keyboard = [[InlineKeyboardButton("Вызвать IT-специалиста", callback_data='call_it')]]
#             reply_markup = InlineKeyboardMarkup(keyboard)

#             # Отправляем сообщение с клавиатурой
#             update.callback_query.message.reply_text("Теперь вы зарегистрированы как преподаватель.", reply_markup=reply_markup)
#         else:
#             update.message.reply_text("Теперь вы зарегистрированы как преподаватель.")
#     else:
#         # Ошибка: пользователь не найден
#         if update.callback_query:
#             update.callback_query.message.reply_text("Ошибка: данные пользователя не найдены. Пожалуйста, сначала пройдите аутентификацию.")
#         else:
#             update.message.reply_text("Ошибка: данные пользователя не найдены. Пожалуйста, сначала пройдите аутентификацию.")

# # Функция для обработки вызова IT-специалиста
# def call_it_handler(update, context):
#     query = update.callback_query
#     query.answer()
#     # Добавьте здесь логику обработки вызова IT-специалиста
#     return create_request(update, context)

# def handle_helpdesk(update, context):
#     query = update.callback_query
#     query.answer()

#     username = context.user_data.get('username')

#     # Проверяем, прошел ли пользователь аутентификацию
#     if username is None:
#         query.edit_message_text('Пожалуйста, сначала пройдите аутентификацию.')
#         return

#     # Проверяем, зарегистрирован ли пользователь уже как Lecturer или Student
#     if Lecturer.objects.filter(username=username).exists() or Student.objects.filter(username=username).exists():
#         query.edit_message_text('Вы уже зарегистрированы в другой роли. Нельзя иметь несколько ролей.')
#         return

#     # Если нет, создаем новую запись HelpDeskUser
#     HelpDeskUser.objects.get_or_create(username=username, defaults={'chat_id': update.effective_chat.id})
#     query.edit_message_text('Профиль сотрудника HelpDesk создан.')


