from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)

    def __str__(self):
        return self.user.username

class Student(models.Model):
    idss = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    registration_date = models.DateField(null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    personal_id = models.CharField(max_length=12, null=True, blank=True)  # ИИН РК
    student_status = models.CharField(max_length=100, null=True, blank=True)
    education_level = models.CharField(max_length=100, null=True, blank=True)
    study_form = models.CharField(max_length=100, null=True, blank=True)  # Форма обучения
    payment_type = models.CharField(max_length=100, null=True, blank=True)  # Вид оплаты
    username = models.EmailField()
    phone = models.CharField(max_length=20, null=True, blank=True)
    specialty = models.CharField(max_length=255, null=True, blank=True)  # Образовательная программа
    op_code = models.CharField(max_length=100, null=True, blank=True)  # Шифр ОП
    gop = models.CharField(max_length=100, null=True, blank=True)  # ГОП
    course = models.IntegerField(null=True, blank=True)  # Курс обучения
    school = models.CharField(max_length=100, null=True, blank=True)
    study_term = models.IntegerField(null=True, blank=True)  # Срок обучения
    department = models.CharField(max_length=100, null=True, blank=True)  # Язык обучения
    gender = models.CharField(max_length=10, null=True, blank=True)
    chat_id = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Студенты"

    def has_all_required_data(self):
        return all([self.full_name, self.course, self.specialty, self.gender, self.department, self.chat_id])
    
    def __str__(self):
        return f'{self.full_name} - {self.course}курс - {self.specialty}'

    
class Advisor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, null=True, blank=True) 
    is_main_advisor = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Эдвайзоры"

    def __str__(self):
        return self.user.username
    
    @property
    def open_requests_count(self):
        return self.user.requests.filter(closed=False).count()
    
class QuickMessage(models.Model):
    text = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = "Быстрые ответы"

    def __str__(self):
        return self.text
    
class Specialty(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
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
    assigned_user = models.ForeignKey(User, related_name='assigned_questions', null=True, on_delete=models.SET_NULL)
    
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

    class Meta:
        verbose_name_plural = "Вопросы студентов"
    
    def __str__(self):
        return str(self.student.full_name)
    
class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()

    class Meta:
        verbose_name_plural = "Вопросы и ответы в Almau Bot"

    def __str__(self):
        return self.question 
    
class Mailing(models.Model):
    students = models.ManyToManyField('Student')
    message = models.TextField()
    file = models.FileField(upload_to='mailings/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Рассылки"

    def __str__(self):
        return f'№{self.id}, {self.created_at.strftime("%d.%m.%Y %H:%M")}'
