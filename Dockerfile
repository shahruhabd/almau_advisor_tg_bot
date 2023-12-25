FROM python:3.11.4

WORKDIR /app
COPY . /app/

RUN apt-get update && apt-get install -y libldap2-dev libsasl2-dev supervisor

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir --default-timeout=120 -r requirements.txt

# Копируем конфигурационный файл supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]