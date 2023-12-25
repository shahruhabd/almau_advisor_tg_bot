from django.db import models
from django.contrib.auth.models import User

class HelpDeskRequest(models.Model):
    auditorium_number = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(User, related_name='created_requests', on_delete=models.CASCADE)
    handler = models.ForeignKey(User, related_name='handled_requests', null=True, blank=True, on_delete=models.SET_NULL)
    conversation = models.JSONField(blank=True, null=True)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    decline_reason = models.TextField(null=True, blank=True)

    NEW = 'NEW'
    IN_PROCESS = 'IN_PROCESS'
    CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (NEW, 'Новая'),
        (IN_PROCESS, 'В обработке'),
        (CLOSED, 'Закрыта'),
    ]
    status = models.CharField(
         max_length=20,
         choices=STATUS_CHOICES,
         default=NEW,
    )

    class Meta:
        verbose_name_plural = "Заявки HelpDesk"

    def __str__(self):
        return f"Заявка №{self.id} от {self.creator.username}, статус {self.status}"

class HelpDeskUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    username = models.CharField(max_length=255, unique=True)
    chat_id = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "HelpDesk staff"

    def __str__(self):
            return f'{self.username}'

class Lecturer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=255, unique=True)
    chat_id = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Преподаватели и Сотрудники"

    def __str__(self):
        return f'{self.username}'