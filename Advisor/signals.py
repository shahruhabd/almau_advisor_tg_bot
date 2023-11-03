from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Question  # Предполагается, что ваша модель Question находится в этом же приложении

channel_layer = get_channel_layer()

@receiver(post_save, sender=Question)
def announce_new_question(sender, instance, created, **kwargs):
    if created:
        async_to_sync(channel_layer.group_send)(
            'questions_default_room',  # Это имя вашей группы веб-сокетов
            {
                'type': 'question_message',
                'question': instance.chat_id,
                'question': instance.student,
                'question': instance.answer,
                'question': instance.created_at,
                'question': instance.answered_at,
                'question': instance.conversation,
                'question': instance.is_closed,
                'question': instance.assigned_user
            }
        )