from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from Advisor.views import *
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls, name=admin),
    path('', home, name='home'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/login.html'), name='logout'),
    path('questions/', show_questions, name='show_questions'),
    path('view_question/<int:question_id>/', view_question, name='view_question'),
    path('ad/', ad_list, name='ad_list'),
    path('mailing/', send_mailing, name='send_mailing'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)