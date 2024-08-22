FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install gunicorn==20.1.0 && \
    pip install -r requirements.txt --no-cache-dir

COPY . ./

RUN python manage.py makemigrations && python manage.py migrate

RUN python manage.py shell -c "from create_admin import create_admin, create_tags, import_ingredients_from_json; create_admin(); create_tags(); import_ingredients_from_json()"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi"]
