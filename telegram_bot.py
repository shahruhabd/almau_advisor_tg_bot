import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Almau_Advisor.settings")
django.setup()
import telegram
from django.conf import settings
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from Advisor.models import Request, Message
from django.contrib.auth import get_user_model

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django.contrib.auth.models import Group, User
from django.db.models import Count, Q

import datetime

# Conversation states
STUDENT_NAME, STUDENT_ID, QUESTION, RATE = range(4)


def start(update, context):
    current_time = datetime.datetime.now().time()

    start_time = datetime.time(9, 0)
    end_time = datetime.time(18, 0)

    if start_time <= current_time <= end_time:
        context.user_data.clear()
        # Check if the user has a previous request
        chat_id = update.effective_chat.id
        request = Request.objects.filter(telegram_chat_id=str(chat_id), closed=True).last()

        if request:

            # Send a message with the previous information and ask for the question
            reply_markup = InlineKeyboardMarkup([
            ])

            message_text = (
                f"Задавайте вопрос:"
            )

            try:
                update.message.reply_text(message_text, reply_markup=reply_markup)
            except AttributeError:
                context.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup)

            return QUESTION
        else:
            # If the user doesn't have a previous request, start from the beginning
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("Студент AlmaU 🍎", callback_data="student")],
                [InlineKeyboardButton("Не студент", callback_data="non_student")]
            ])

            try:
                update.message.reply_text("Кто вы?", reply_markup=reply_markup)
            except AttributeError:
                context.bot.send_message(chat_id=chat_id, text="Кто вы?", reply_markup=reply_markup)

    else:
        # Если текущее время вне рабочего интервала, отправьте сообщение пользователю
        update.message.reply_text("Бот работает с 9:00 до 18:00. Пожалуйста, обратитесь в рабочее время.")

def handle_student_name(update, context):
    update.message.reply_text("Пожалуйста, введите ваше имя:")
    return STUDENT_ID  # переходим к следующему состоянию

def handle_student_id(update, context):
    student_name = update.message.text
    context.user_data['student_name'] = student_name  # сохраняем имя студента

    update.message.reply_text("Пожалуйста, введите ваш ID:")
    return QUESTION  # переходим к состоянию вопроса

def handle_message(update, context):
    advisor_group = Group.objects.get(name='Advisor')
    advisor_users = advisor_group.user_set.annotate(num_requests=Count('assigned_requests')).order_by('num_requests')
    assigned_user = advisor_users.first()

    current_time = datetime.datetime.now().time()

    start_time = datetime.time(9, 0)  # Начало рабочего дня
    end_time = datetime.time(19, 0)   # Конец рабочего дня

    if start_time <= current_time <= end_time:
        text = update.message.text
        chat_id = update.effective_chat.id

        # Получение имени отправителя из Telegram
        author = update.message.from_user.username or 'Неизвестный автор'

        # Получаем текущее состояние пользователя
        state = context.user_data.get('state')
        print(f"Current state: {state}")

        if state == QUESTION:

            request = Request.objects.create(
                author=author,
                telegram_chat_id=str(chat_id),
                assigned_user=assigned_user
            )
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "requests_group",
                {
                    "type": "request_notification",
                    "message": {
                        "type": "new_request",
                        "data": {
                            "request_id": request.id,
                            "author": author,
                        }
                    },
                },
            )
            
            user, _ = get_user_model().objects.get_or_create(username=author)
            message = Message.objects.create(
                user=user,
                request=request,
                content=text,
                author=author
            )

            # Отправляем уведомление через WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "requests_group",  # Группа WebSocket-подключений
                {
                    "type": "request_notification",
                    "message": {
                        "type": "new_request",
                        "data": {
                            "request_id": request.id,
                            "author": author,
                            # Добавьте другие поля вашей заявки, если они есть
                        }
                    },
                },
            )


            # Отправляем уведомление администратору
            admin_message = f"Новый вопрос:\n\n{author}: {text}"
            admin_chat_id = settings.ADMIN_TELEGRAM_CHAT_ID
            context.bot.send_message(chat_id=admin_chat_id, text=admin_message)

            context.bot.send_message(chat_id=chat_id, text="Ваш вопрос отправлен администратору! Ожидайте ответа.")
        elif state == RATE:
            return ConversationHandler.END
        else:
            # Получаем текущую заявку пользователя (если она есть)
            request = Request.objects.filter(telegram_chat_id=str(chat_id), closed=False).first()

            if request:
                # Если заявка найдена и не закрыта, добавляем сообщение к существующей заявке
                user, _ = get_user_model().objects.get_or_create(username=author)
                message = Message.objects.create(
                    user=user,
                    request=request,
                    content=text,
                    author=author
                )
                context.bot.send_message(chat_id=chat_id, text="Сообщение сохранено! Ожидайте ответа!")
            else:
                # Если заявка не найдена или уже закрыта, создаем новую заявку
                request = Request.objects.create(
                    author=author,
                    telegram_chat_id=str(chat_id),
                    assigned_user=assigned_user
                )
                user, _ = get_user_model().objects.get_or_create(username=author)
                message = Message.objects.create(
                    user=user,
                    request=request,
                    content=text,
                    author=author
                )
                context.bot.send_message(chat_id=chat_id, text="Заявка создана и сообщение сохранено!")
    else:
        # Если текущее время вне рабочего интервала, отправьте сообщение пользователю
        update.message.reply_text("Бот работает с 9:00 до 18:00. Пожалуйста, обратитесь в рабочее время.")

def close_chat(update, context):
    chat_id = update.effective_chat.id
    request = Request.objects.filter(telegram_chat_id=str(chat_id), closed=False).first()
    if request and not request.closed:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Да", callback_data="yes")],
            [InlineKeyboardButton("Нет", callback_data="no")]
        ])
        update.message.reply_text("Помог ли вам эдвайзер?", reply_markup=reply_markup)
        return RATE
    else:
        update.message.reply_text("Произошла ошибка. Не удалось закрыть чат.")
        return ConversationHandler.END 


def handle_rate(update, context):
    query = update.callback_query
    answer = query.data
    chat_id = update.effective_chat.id
    request = Request.objects.filter(telegram_chat_id=str(chat_id), closed=False).first()

    if request and not request.closed:
        if answer == "yes":
            print('call back yes')
            request.closed = True
            request.save()
            query.edit_message_text("Спасибо за ваш ответ. Заявка закрыта.")
        elif answer == "no":
            print('call back no')
            main_advisor_group = Group.objects.get(name='Main Advisor')
            main_advisor_user = main_advisor_group.user_set.first()
            if main_advisor_user:
                request.assigned_user = main_advisor_user
                request.save()
                query.edit_message_text("Спасибо за ваш ответ. Ваша заявка будет переназначена.")
            else:
                query.edit_message_text("Произошла ошибка. Не удалось переназначить заявку.")
        return ConversationHandler.END
    else:
        query.edit_message_text("Произошла ошибка. Не удалось закрыть чат или оценить сервис.")
        return ConversationHandler.END

def main():
    updater = Updater(token=settings.TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("close", close_chat))

    # Обработчик всех входящих сообщений
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # ConversationHandler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GENDER: [CallbackQueryHandler(handle_gender)],
            STUDENT_NAME: [MessageHandler(Filters.text, handle_student_name)],
            STUDENT_ID: [MessageHandler(Filters.text, handle_student_id)],
            QUESTION: [MessageHandler(Filters.text, handle_message)],
            RATE: [CallbackQueryHandler(handle_rate)]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    dispatcher.add_handler(conversation_handler)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()