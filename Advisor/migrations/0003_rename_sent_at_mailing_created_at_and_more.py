# Generated by Django 4.2.2 on 2023-11-01 04:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Advisor", "0002_mailing"),
    ]

    operations = [
        migrations.RenameField(
            model_name="mailing",
            old_name="sent_at",
            new_name="created_at",
        ),
        migrations.RemoveField(
            model_name="mailing",
            name="chat_ids",
        ),
        migrations.RemoveField(
            model_name="mailing",
            name="image",
        ),
        migrations.AddField(
            model_name="mailing",
            name="file",
            field=models.FileField(blank=True, null=True, upload_to="mailing_files/"),
        ),
        migrations.AddField(
            model_name="mailing",
            name="students",
            field=models.ManyToManyField(to="Advisor.student"),
        ),
    ]