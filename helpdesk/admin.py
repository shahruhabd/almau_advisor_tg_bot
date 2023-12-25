from django.contrib import admin
from .models import HelpDeskRequest, Lecturer, HelpDeskUser

admin.site.register(HelpDeskRequest)
admin.site.register(Lecturer)
admin.site.register(HelpDeskUser)