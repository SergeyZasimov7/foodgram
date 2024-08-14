import json
import os
import sys

from django.contrib.auth.models import User
from django.core.management import execute_from_command_line

from recipes.models import Ingredient, Tag


def create_admin():
    admin_username = 'admin'
    admin_password = '28GjxJceRfp'
    admin_email = 'admin@example.com'
    admin_first_name = 'Admin'
    admin_last_name = 'Admin'

    try:
        User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            first_name=admin_first_name,
            last_name=admin_last_name,
        )
        print("Администратор создан!")
    except Exception as e:
        print(f"Ошибка создания администратора: {e}")


def create_tags():
    tags = [
        {'name': 'Завтрак', 'slug': 'zavtrak'},
        {'name': 'Обед', 'slug': 'obed'},
        {'name': 'Ужин', 'slug': 'uzhin'},
        {'name': 'Десерты', 'slug': 'deserty'},
        {'name': 'Вегетарианские', 'slug': 'vegetarianskye'},
        {'name': 'Мясные блюда', 'slug': 'myasnye_blyuda'},
    ]

    try:
        for tag in tags:
            Tag.objects.create(
                name=tag['name'],
                slug=tag['slug']
            )
        print("Теги созданы!")
    except Exception as e:
        print(f"Ошибка создания тегов: {e}")


def import_ingredients_from_json():
    file_path = 'data/ingredients.json'
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            try:
                Ingredient.objects.get(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
            except Ingredient.DoesNotExist:
                Ingredient.objects.create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
        print("Ингредиенты импортированы!")


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
    )
    execute_from_command_line([
        'manage.py',
        'shell',
        '-c',
        """
        from create_admin import
        create_admin,
        create_tags,
        import_ingredients_from_json;
        create_admin();
        create_tags();
        import_ingredients_from_json()
        """
    ])
