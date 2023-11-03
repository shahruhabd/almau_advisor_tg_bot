from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from Advisor.views import *

urlpatterns = [
    path('admin/', admin.site.urls, name=admin),
    path('', home, name='home'),
    path('login_success/', login_success, name='login_success'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/login.html'), name='logout'),
    path('login-ad/', login_view, name='login_view'),
    path('questions/', show_questions, name='show_questions'),
    path('questions/', show_questions, name='show_questions'),
    path('view_question/<int:question_id>/', view_question, name='view_question'),
    path('ad/', ad_list, name='ad_list')


    # path('chat/<str:room_name>/', room, name='room'),




    # path('ws/requests/<int:request_id>/', consumers.RequestConsumer.as_asgi()),
]
    # path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'), name='password_change'),
    # path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
