# Generated by Django 4.2.2 on 2023-10-24 04:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("Advisor", "0012_question_is_closed"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="request",
            name="assigned_user",
        ),
        migrations.AddField(
            model_name="question",
            name="assigned_user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_requests",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]