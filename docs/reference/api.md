# API

Обычный клиент работает с API веба на http://localhost:8090. Для доступа к истории нужна cookie гостевой сессии. Сохраните её между запросами.

## Загрузить и получить результат

```sh
curl -c /tmp/lectern-cookies.txt http://localhost:8090/api/me
curl -b /tmp/lectern-cookies.txt -c /tmp/lectern-cookies.txt   -F file=@lesson.mp3 http://localhost:8090/api/generations/upload
```

Успешная загрузка возвращает HTTP 201 и объект с полем id. Это подтверждает приём файла; обработка ещё может завершиться ошибкой.

```json
{"id": "gen_example", "content_hash": "...", "cache_hit": false}
```

Подставьте полученный id:

```sh
curl -b /tmp/lectern-cookies.txt   http://localhost:8090/api/generations/gen_example
```

## Основные маршруты веба

| Метод и путь | Результат |
|---|---|
| GET /api/config | Режим распознавания и флаг генерации материалов |
| GET /api/me | Идентификатор гостевой сессии |
| GET /api/generations | До 20 последних результатов текущей сессии |
| POST /api/generations/upload | Multipart-поле file; регистрация обработки |
| GET /api/generations/{id} | Статус, транскрипт и сохранённые материалы |
| POST /api/generations/{id}/retry | Повторная генерация из сохранённого транскрипта |
| DELETE /api/generations/{id} | Отмена веб-задачи и удаление результата владельца; при наличии ответов учеников возможна ошибка |
| PATCH /api/generations/{id} | Сохранение правок конспекта, теста или аналитики |

Для проверки всей цепочки в режиме demo используйте python scripts/smoke.py из [руководства разработчика](../development.md).

## Формат локальной реплики

Время в ответе веба указано в миллисекундах. Пример ниже синтетический.

```json
{
  "start_ms": 12400,
  "end_ms": 18900,
  "speaker": "Преподаватель",
  "speaker_id": 0,
  "source_speaker": "SPEAKER_00",
  "role": "teacher",
  "text": "Почему здесь меняется знак?"
}
```

Числовые показатели speech находятся в analytics.local_speech. Поле analytics.synthetic помечает демо. Набор учебных материалов зависит от режима и результата генерации.

## Внутренние API

speech принимает POST /transcribe с multipart-полем file и возвращает timeline в секундах вместе с analytics. Этот запрос ждёт завершения обработки. Доступный GET /health проверяет процесс API без обязательной загрузки моделей.

ml принимает задания, возвращает HTTP 202 с job_id, затем отдаёт статус через GET /tasks/{job_id}. Эти запросы требуют заголовок X-API-Key. Схема маршрутов доступна в /docs каждого сервиса внутри контейнерной сети; их порты наружу не опубликованы.

Веб не использует старые маршруты speech для потока и истории. У них иные правила хранения; не подключайте их как замену /transcribe без отдельной проверки.
