from django.db import models

from django.contrib.auth.models import User

# Модель для работника службы поддержки
class HelpDeskWorker(models.Model):
    user = models.ForeignKey(User, related_name='help_desk_user', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)

    def __str__(self):
        return self.full_name

# Модель для запросов в службу поддержки
class HelpDeskRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('processing', 'В обработке'),
        ('closed', 'Закрытая')
    ]
    employee = models.ForeignKey(User, related_name='employee', on_delete=models.SET_NULL, null=True)
    text = models.TextField(max_length=100)
    assigned_user = models.ForeignKey(HelpDeskWorker, related_name='requests', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    auditorium = models.IntegerField()

    def __str__(self):
        return f"Аудитории - {self.auditorium}, Сотрудник - {self.employee}"