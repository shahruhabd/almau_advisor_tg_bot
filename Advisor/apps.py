from django.apps import AppConfig


class AdvisorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Advisor'

    def ready(self):
        import Advisor.signals
