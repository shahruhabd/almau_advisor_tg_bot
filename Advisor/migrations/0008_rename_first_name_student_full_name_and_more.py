# Generated by Django 4.2.2 on 2023-10-23 04:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Advisor", "0007_student_specialty"),
    ]

    operations = [
        migrations.RenameField(
            model_name="student",
            old_name="first_name",
            new_name="full_name",
        ),
        migrations.RemoveField(
            model_name="student",
            name="last_name",
        ),
        migrations.AddField(
            model_name="student",
            name="course",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="student",
            name="specialty",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]