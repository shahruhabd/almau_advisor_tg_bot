# Generated by Django 5.0 on 2023-12-21 11:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Advisor", "0006_alter_question_assigned_user"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="advisor",
            options={"verbose_name_plural": "Эдвайзоры"},
        ),
        migrations.AlterModelOptions(
            name="faq",
            options={"verbose_name_plural": "Вопросы и ответы в Almau Bot"},
        ),
        migrations.AlterModelOptions(
            name="mailing",
            options={"verbose_name_plural": "Рассылки"},
        ),
        migrations.AlterModelOptions(
            name="question",
            options={"verbose_name_plural": "Вопросы студентов"},
        ),
        migrations.AlterModelOptions(
            name="quickmessage",
            options={"verbose_name_plural": "Быстрые ответы"},
        ),
        migrations.AlterModelOptions(
            name="student",
            options={"verbose_name_plural": "Студенты"},
        ),
        migrations.AddField(
            model_name="advisor",
            name="full_name",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
