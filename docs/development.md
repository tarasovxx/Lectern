# Разработка

## Окружение приложения

Для проверок приложения используйте Python 3.11 или 3.12. Из корня репозитория выполните:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
make test
make config
```

Тесты запускаются без GPU и без скачивания моделей. Наборы web, ml и speech выполняются в разных процессах: два сервиса используют одинаковое имя Python-пакета app.

После запуска make demo доступна сквозная HTTP-проверка:

```sh
python scripts/smoke.py
```

Она проверяет страницу, загрузку, готовый транскрипт, аналитику и удаление. Ей нужен именно режим demo. Для другого порта задайте переменную LECTERN_URL, например http://127.0.0.1:8091.

## Документация

Для сайта используйте отдельное окружение Python 3.12:

```sh
python3 -m venv .venv-docs
. .venv-docs/bin/activate
pip install -r requirements-docs.txt
make docs
```

Откройте [localhost:8001](http://localhost:8001). MkDocs обновляет страницу при изменении Markdown.

```sh
make docs-build
```

Статический сайт окажется в site/. Строгая сборка завершается ошибкой при предупреждениях, отсутствующей странице или неверной внутренней ссылке. Генерируемый каталог не входит в Git.

Редактируйте страницы внутри docs/. Навигация и расширения Markdown заданы в mkdocs.yml. Mermaid-схемы находятся в ограждённых блоках mermaid; меняйте их вместе с описываемым поведением. Интерактивная карта имеет отдельный исходник в maintenance/diagrams. Для её пересборки нужен [Archify](https://archify.si). Команда из корня репозитория после установки навыка:

```sh
node ~/.codex/skills/archify/bin/archify.mjs finalize architecture \
  maintenance/diagrams/architecture.json \
  docs/assets/diagrams/architecture.html \
  --repo-root . --quality showcase --out-dir /tmp/lectern-archify-check --json
```

После изменения карты обновите исходник, HTML и отчёт проверки вместе. Archify не нужен для обычной сборки MkDocs: готовый HTML уже включён в docs.

## Что проверяет CI

Workflow CPU checks запускает тесты, проверяет Compose, собирает web и ml и выполняет HTTP-сценарий демо. Он не собирает тяжёлые речевые образы и не измеряет качество распознавания.

Workflow Documentation выполняет строгую сборку сайта и прикладывает архив lectern-docs к запуску GitHub Actions. Сам по себе этот workflow не публикует сайт в GitHub Pages.

## Структура репозитория

| Каталог | Назначение |
|---|---|
| services/web | Интерфейсы, SQLite, очередь и адаптер речевого сервиса |
| services/speech | Локальные модели и аналитика речи |
| services/ml | Задания генерации и облачные провайдеры |
| docs | Страницы сайта и схемы |
| scripts | Запуск наборов тестов и HTTP-проверка |
| maintenance | Исторические записи интеграции, реестр происхождения кода, исходники интерактивных схем |

При изменении API обновляйте [справочник](reference/api.md) и схему обработки. При изменении Compose сверяйте [настройки](reference/configuration.md) и команды запуска.
