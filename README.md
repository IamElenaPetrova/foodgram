# Foodgram <br>
Foodgram - приложение, где пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.<br><br>
Автор: Елена Петрова https://github.com/IamElenaPetrova <br>
### Функционал
<ul>
  <li>Публикация рецептов с добавлением фото, выбором ингредиентов и метками тегов
  <li>Подписка на авторов
  <li>Добавление рецептов в избранное
  <li>Сервис "Список покупок" - формирование PDF-файла со списком продуктов
  <li>Безопасная аутентификация и авторизация
</ul>

### Стек
  <ul>
    <li>Python 3.9
    <li>Django 3.2.3 - веб-фрэймворк
    <li>Djano REST Framework - API
    <li>PostgreSQL, SQLite - база данных
    <li>Gunicorn - WSGI-сервер
    <li>Docker, Docker Compose, Docker Hub - контейнерезация
    <li>Nginx - веб-сервер и прокси
    <li>GitHub Actions - CI/CD
  </ul>


### Доступные эндпойнты
- api/users/ - список пользователей, регистрация пользователя
- api/users/id/ - профиль пользователя
- api/users/me/ - профиль текущего пользователя
- api/users/me/avatar/ - добавление и удаление аватара
- api/users/set_password/ - изменение пароля
- api/auth/token/login/ - вход
- api/auth/token/logout/ - выход
- api/tags/ - список тегов
- api/tags/{id}/ - информация о теге
- api/recipes/ - список всех рецептов, создание рецепта
- api/recipes/{id}/ - просмотр, редактирование или удаление рецепта
- api/recipes/{id}/get-link/ - короткая ссылка на рецепт
- api/recipes/download_shopping_cart/ - загрузить файл со списком покупок
- api/recipes/{id}/shopping_cart/ - добавить/удалить рецепт из списка покупок
- api/recipes/{id}/favorite/ - добавить/удалить рецепт из избранного
- api/users/subscriptions/ - список подписок текущего пользователя
- api/users/{id}/subscribe/ - подписаться/отписаться на пользователя
- api/ingredients/ - список всех ингредиентов
- api/ingredients/{id}/ - информация о конкретном ингредиенте

### Как развернуть проект
Клонировать репозиторий и перейти в него в командной строке:<br>
<br>
```
git clone git@github.com:IamElenaPetrova/foodgram.git
```
Перейти в каталог проекта:
```
cd foodgram
```
Создать .env:
```
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432
DEBUG=FALSE
SECRET_KEY=my-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_SQLITE=FALSE
```
Развернуть приложение:
```
docker-compose up --build
```

Проект станет доступен на локальном IP `127.0.0.1:8010`.

