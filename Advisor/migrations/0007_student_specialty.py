# Generated by Django 4.2.2 on 2023-10-23 03:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("Advisor", "0006_specialty"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="specialty",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="Advisor.specialty",
            ),
        ),
    ]