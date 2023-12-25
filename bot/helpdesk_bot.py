# from telegram import InlineKeyboardButton, InlineKeyboardMarkup
# from helpdesk.models import HelpDeskRequest

# # Функция для создания клавиатуры HelpDesk
# def helpdesk_keyboard():
#     keyboard = [
#         [InlineKeyboardButton("Посмотреть заявки", callback_data='view_requests')]
#     ]
#     return InlineKeyboardMarkup(keyboard)

# # Обработчик для кнопки "Посмотреть заявки"
# def view_requests(update, context):
#     query = update.callback_query
#     query.answer()
    
#     requests = HelpDeskRequest.objects.all()
#     message_text = "Список заявок:\n\n"
    
#     for request in requests:
#         message_text += f"ID: {request.id}, Аудитория: {request.auditorium_number}, Описание: {request.description}\n"
    
#     query.edit_message_text(text=message_text)

# # Добавьте обработчик CallbackQueryHandler в Dispatcher
# # dp.add_handler(CallbackQueryHandler(view_requests, pattern='^view_requests$'))

# # После успешной авторизации как HelpDesk, показать эту клавиатуру
# # update.message.reply_text('Выберите действие:', reply_markup=helpdesk_keyboard())
