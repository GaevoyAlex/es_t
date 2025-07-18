# liberandum_fastapi_frontend



## Запуск контейнера

Для начала сбилдить:
```sh
docker-compose up --build
```

Потом делат началные миграции, запуск команды при запущенном контейнере.

```sh
docker-compose exec api bash -c "alembic revision --autogenerate -m 'Create users table'"
```

Уже потом также применяем миграции:

```sh
docker-compose exec api bash -c "alembic upgrade head"
```