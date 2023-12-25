from django.contrib import admin
from django.urls import path
from Advisor.views import *

urlpatterns = [
    path('admin/', admin.site.urls, name=admin),
    path('', home, name='home'),
    path('logout/', logout_request, name='logout'),
    path('questions/', show_questions, name='show_questions'),
    path('questions/json/', get_questions_json, name='questions-json'),
    path('get_total_questions_count/json/', get_total_questions_count, name='get_total_questions_count'),
    path('view_question/<int:question_id>/', view_question, name='view_question'),
    path('get_chat_data/<int:question_id>/', get_chat_data, name='get_chat_data'),
    path('ad/', ad_list, name='ad_list'),
    path('send_mailing/', send_mailing, name='send_mailing'),
    path('profile/', update_profile, name='update_profile'),
    path('import-students/', import_students_view, name='import-students'),
]