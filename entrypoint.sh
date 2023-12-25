#!/bin/bash
# Выполнение команд Django
python manage.py migrate
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='root').exists() or User.objects.create_superuser('root', 'root@example.com', 'root')"
python manage.py collectstatic --no-input

# Запуск supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
