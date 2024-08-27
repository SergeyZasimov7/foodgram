[![GitHub Actions](https://github.com/SergeyZasimov7/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/SergeyZasimov7/foodgram/actions)

https://task.sytes.net/ - сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

### Стек технологий

Backend: Python (Flask), PostgreSQL
Frontend: HTML, CSS, JavaScript
Инфраструктура: Docker, GitHub Actions, Nginx 

### Как развернуть проект

1. Клонируйте репозиторий:
git clone https://github.com/SergeyZasimov7/foodgram


2. Создайте виртуальное окружение:
python3 -m venv venv
source venv/Scripts/activate


3. Установите зависимости:
pip install -r backend/requirements.txt


4. Заполните файл .env:
# PostgreSQL connection details
POSTGRES_DB=your_db
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
DB_NAME=your_db

# Secret key for Flask
SECRET_KEY=your_secret_key

5. В корневой папке выполнить следующую команду:
docker compose -f docker-compose.yml up -d 

6. База данных автоматически заполняется нужными данными благодаря следующей команды, прописанной в Dockerfile(backend):
RUN python manage.py shell -c "from create_admin import create_admin, create_tags, import_ingredients_from_json; create_admin(); create_tags(); import_ingredients_from_json()"

<h3 align="center">
    <a href="http://task.sytes.net">Сайта</a><p></p>
    <a href="http://task.sytes.net/api/docs/">Документация</a>
</h3>


## Пример запросов/ответов

#### Get item

```http
  GET /api/recipes/{id}/
```

| Parameter | Type     | Description                                                            |
| :-------- | :------- |:-----------------------------------------------------------------------|
| `id`| `string` | **Required**. Уникальный идентификатор этого рецепта|
| `tags` | `Array of strings` | Показывать рецепты только с указанными тегами (по slug)|
| `author` | `integer` | Показывать рецепты только автора с указанным id.|
| `ingredients` | `integer` | Показывать ингридиенты рецепта с указанным id.|
| `is_favorited` | `boolean` | Варианты: `true` `false`. Показывать только рецепты, находящиеся в списке избранного. |
| `is_in_shopping_cart` | `boolean` | Варианты: `true` `false`. Показывать только рецепты, находящиеся в списке покупок. |

<details>
<summary>Response</summary>

```json
{
    "id": 1,
    "tags": [
        {
            "id": 1,
            "name": "Завтрак",
            "slug": "zavtrak"
        }
    ],
    "author": {
        "id": 2,
        "username": "sergey",
        "first_name": "Сергей",
        "last_name": "Засимов",
        "email": "sergey@mail.ru",
        "is_subscribed": false,
        "avatar": "http://task.sytes.net/media/avatars/2911b114-e935-4566-8c4b-18458abbc822.jpeg"
    },
    "ingredients": [
        {
            "id": 1788,
            "name": "сыр твердый",
            "measurement_unit": "г",
            "amount": 300
        },
        {
            "id": 2180,
            "name": "яйца куриные",
            "measurement_unit": "г",
            "amount": 30
        },
        {
            "id": 1081,
            "name": "мука",
            "measurement_unit": "г",
            "amount": 30
        },
        {
            "id": 980,
            "name": "масло для фритюра",
            "measurement_unit": "мл",
            "amount": 70
        }
    ],
    "is_favorited": false,
    "is_in_shopping_cart": false,
    "name": "Домашние сырные палочки",
    "image": "http://task.sytes.net/media/recipes/f3025663-9153-4efc-91b1-45221a83bbd5.jpg",
    "text": "Приготовим продукты для сырных палочек:\nСыр натереть на мелкой терке, добавить муку, яйцо. Перемешать.\nСформировать сырные палочки.\nОбжарить их в растительном масле до золотистого цвета.\nСырные палочки готовы! Приятного аппетита!",
    "cooking_time": 30
}
```
</details>

### Автор

 - [Сергей Засимов](https://github.com/SergeyZasimov7)
