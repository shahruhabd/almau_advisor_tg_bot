from django.contrib import admin
from Advisor.models import *

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'course', 'specialty', 'gender', 'department']
    search_fields = ['full_name', 'username', 'specialty', 'school']
admin.site.register(Question)
admin.site.register(Advisor)
admin.site.register(QuickMessage)
admin.site.register(Mailing)
admin.site.register(UserProfile)
admin.site.register(FAQ)
