# Generated by Django 5.0 on 2023-12-13 03:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Advisor', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentImport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idss', models.CharField(blank=True, max_length=100, null=True)),
                ('country', models.CharField(blank=True, max_length=100, null=True)),
                ('registration_date', models.DateField(blank=True, null=True)),
                ('full_name', models.CharField(blank=True, max_length=255, null=True)),
                ('personal_id', models.CharField(blank=True, max_length=12, null=True)),
                ('student_status', models.CharField(blank=True, max_length=100, null=True)),
                ('education_level', models.CharField(blank=True, max_length=100, null=True)),
                ('study_form', models.CharField(blank=True, max_length=100, null=True)),
                ('payment_type', models.CharField(blank=True, max_length=100, null=True)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('education_program', models.CharField(blank=True, max_length=255, null=True)),
                ('op_code', models.CharField(blank=True, max_length=100, null=True)),
                ('gop', models.CharField(blank=True, max_length=100, null=True)),
                ('course', models.IntegerField()),
                ('department', models.CharField(blank=True, max_length=100, null=True)),
                ('study_term', models.IntegerField()),
                ('language', models.CharField(blank=True, max_length=100, null=True)),
                ('gender', models.CharField(blank=True, max_length=10, null=True)),
            ],
        ),
    ]
