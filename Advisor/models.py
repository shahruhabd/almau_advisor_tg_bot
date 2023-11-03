from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.contrib.postgres.fields import JSONField

class Advisor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_main_advisor = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    
    @property
    def open_requests_count(self):
        return self.user.requests.filter(closed=False).count()
    
class QuickMessage(models.Model):
    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text
    
class Specialty(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class Student(models.Model):
    username = models.CharField(max_length=255, unique=True)
    chat_id = models.IntegerField(null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    course = models.IntegerField(null=True, blank=True)
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username
    
class Chat(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='chats')
    
class Question(models.Model):
    chat_id = models.ForeignKey(Chat, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='questions')
    answer = models.TextField(blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    conversation = models.JSONField(blank=True, null=True)
    is_closed = models.BooleanField(default=False)
    assigned_user = models.ForeignKey(User, related_name='assigned_requests', null=True, on_delete=models.SET_NULL)
    
    NEW = 'NEW'
    IN_PROCESS = 'IN_PROCESS'
    CLOSED = 'CLOSED'
    MAIN_ADVISOR = 'MAIN_ADVISOR'

    STATUS_CHOICES = [
        (NEW, 'Новая'),
        (IN_PROCESS, 'В обработке'),
        (CLOSED, 'Закрыта'),
        (MAIN_ADVISOR, 'У главы ЭЦ')
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=NEW,
    )

    
    def __str__(self):
        return str(self.student.full_name)
    
class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return self.question 
    
class Mailing(models.Model):
    students = models.ManyToManyField('Student')
    message = models.TextField()
    file = models.FileField(upload_to='mailings/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)