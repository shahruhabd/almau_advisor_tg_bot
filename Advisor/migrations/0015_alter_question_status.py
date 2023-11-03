# Generated by Django 4.2.2 on 2023-10-26 09:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Advisor", "0014_remove_message_request_remove_message_user_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="question",
            name="status",
            field=models.CharField(
                choices=[
                    ("NEW", "Новая"),
                    ("IN_PROCESS", "В обработке"),
                    ("CLOSED", "Закрыта"),
                    ("MAIN_ADVISOR", "У главы ЭЦ"),
                ],
                default="NEW",
                max_length=20,
            ),
        ),
    ]