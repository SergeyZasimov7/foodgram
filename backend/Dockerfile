FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install gunicorn==20.1.0 && \
    pip install -r requirements.txt --no-cache-dir

COPY . ./

ENV ALLOWED_HOSTS='127.0.0.1,localhost,158.160.64.88,taski.sytes.net'
ENV SECRET_KEY=django-insecure-**e^f2@ma6$dt$d(l+5u#i%iuvzn0q(%^1)r^b!o^b8zf195cb

RUN python manage.py makemigrations && python manage.py migrate

# Run initial data loading, including creating admin user and tags
RUN python manage.py shell -c "from create_admin import create_admin, create_tags, import_ingredients_from_json; create_admin(); create_tags(); import_ingredients_from_json()"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi"]