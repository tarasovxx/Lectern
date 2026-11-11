# LEctern

LEctern превращает запись занятия в расшифровку с таймкодами, ролями говорящих и показателями участия. Речь можно обрабатывать локально. Конспекты и тесты подключаются отдельно.

## Быстрый запуск

Нужны Docker и Docker Compose v2.30+.

```sh
cp .env.example .env
make demo
```

Откройте [localhost:8090](http://localhost:8090). Демо использует синтетический транскрипт: содержимое загруженного файла не распознаётся.

Для своей записи используйте [локальный режим](docs/guides/local.md). Поддержка NVIDIA GPU вынесена в отдельную конфигурацию.

## Документация

[Начать с руководства](docs/index.md) · [Архитектура](docs/architecture/index.md) · [Настройки](docs/reference/configuration.md) · [API](docs/reference/api.md)

Документация собрана на Material for MkDocs. Чтобы открыть её как сайт, создайте Python-окружение:

```sh
python3 -m venv .venv-docs
. .venv-docs/bin/activate
pip install -r requirements-docs.txt
make docs
```

Сайт откроется на [localhost:8001](http://localhost:8001). Статическая сборка: `make docs-build`.

## Разработка

[Установка окружения и проверки](docs/development.md). Полный набор тестов запускается командой `make test`.

Распознавание методических приёмов и качество рекомендаций ещё требуют проверки на размеченных данных. Для следующего этапа нужен [набор материалов для пилота](docs/pilot.md).
