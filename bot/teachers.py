# from django.contrib.auth.models import User
# from django.core.exceptions import ObjectDoesNotExist
# from helpdesk.models import HelpDeskRequest
# from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, Filters, CommandHandler
# from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# import ldap3

# AD_SERVER = 'ldap://dca.iab.kz'


# # Функции для аутентификации преподавателя
# def start_teacher_authentication(update, context):
#     if 'authenticated' in context.user_data:
#         text = 'Вы уже авторизованы.'
#     else:
#         text = 'Введите ваш логин:'

#     # Проверяем, вызван ли обработчик через callback query
#     if update.callback_query:
#         update.callback_query.message.reply_text(text)
#     else:
#         # Если нет, то это обычное текстовое сообщение
#         update.message.reply_text(text)
#     return "AWAITING_USERNAME"


# def receive_teacher_username(update, context):
#     username = update.message.text
#     if "@almau.edu.kz" not in username:
#         username += "@almau.edu.kz"
#     context.user_data['auth_username'] = username
#     update.message.reply_text("Пожалуйста, введите ваш пароль.")
#     print("Перешли в состояние AWAITING_PASSWORD")
#     return "AWAITING_PASSWORD"

# def receive_teacher_password(update, context):
#     username = context.user_data['auth_username']
#     password = update.message.text
#     if check_ad_credentials(AD_SERVER, username, password):
#         user, created = User.objects.get_or_create(username=username)
#         if created:
#             user.set_password(password)
#             user.save()
#         context.user_data['user'] = user
#         context.user_data['authenticated'] = True
#         update.message.reply_text("Вы успешно аутентифицированы.")
#         print(f'{username} авторизован')
#         return show_teacher_menu(update, context)
#     else:
#         update.message.reply_text("Неверные учетные данные.")
#     return ConversationHandler.END

# # Функция для отображения меню преподавателя
# def show_teacher_menu(update, context):
#     keyboard = [[InlineKeyboardButton("Вызвать IT специалиста", callback_data='create_request')]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     update.message.reply_text('Выберите действие:', reply_markup=reply_markup)
#     return TYPING_DESCRIPTION

# # Константы для состояний
# TYPING_DESCRIPTION, CHOOSING_AUDITORIUM, SAVE_REQUEST = range(3)

# def create_request(update, context):
#     if 'authenticated' in context.user_data:
#         update.callback_query.edit_message_text('Опишите проблему:')
#         return CHOOSING_AUDITORIUM
#     else: 
#         update.callback_query.edit_message_text('Вы должны сначала авторизоваться /auth')


# def choose_auditorium(update, context):
#     context.user_data['description'] = update.message.text
#     update.message.reply_text('Введите номер аудитории:')
#     return SAVE_REQUEST

# def save_request(update, context):
#     username = context.user_data.get('username')
#     if not username:
#         update.message.reply_text('Ошибка: отсутствует имя пользователя.')
#         return ConversationHandler.END

#     try:
#         # Поиск пользователя в базе данных по имени пользователя
#         user = User.objects.get(username=username)
#     except User.DoesNotExist:
#         update.message.reply_text('Ошибка: пользователь не найден.')
#         return ConversationHandler.END
    
#     HelpDeskRequest.objects.create(
#         auditorium_number=update.message.text,
#         description=context.user_data['description'],
#         creator=user
#     )
#     update.message.reply_text('Ваша заявка создана, ожидайте.')
#     return ConversationHandler.END

# def check_ad_credentials(AD_SERVER, username, password):
#     with ldap3.Connection(AD_SERVER, user=username, password=password) as conn:
#         return conn.bind()


