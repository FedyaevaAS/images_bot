# Images_bot
### Описание
Небольшой сервис в виде Telegram чат-бота, который пулучает на вход ссылку на picsum.photos, обрабатывает ее и сохраняет изображение за пользователем.
### Как запустить проект

- Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/FedyaevaAS/images_bot
``` 
```
cd images_bot
``` 

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```
```
source venv/scripts/activate
```

- Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

- Применить миграции базы данных:

```
alembic upgrade head
```


Создать в корневой директории файл .env :

```
BOT_TOKEN=<токен бота>
```

- Запустить проект:
```
py run_bot.py
```

### Автор
Федяева Анастасия
