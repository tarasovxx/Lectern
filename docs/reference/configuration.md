# Настройки

Создайте .env из .env.example в корне репозитория. После изменения настроек пересоздайте сервисы командой нужного режима. Файл .env не входит в Git.

## Команды запуска

| Команда | Распознавание | Материалы |
|---|---|---|
| make demo | Синтетический пример, только web | Отключены |
| make local | speech на CPU | Отключены |
| make gpu | speech на NVIDIA GPU | Отключены |
| make materials | speech на CPU | Локальный сервер модели через ml |
| make cloud | Groq через ml | Gemini через ml |

Команды Make явно задают режим веба. Например, make demo запускает демо даже при TRANSCRIPTION_BACKEND=local в .env. Перед сменой режима выполните make stop, чтобы не оставлять ненужные контейнеры.

## Пользовательские настройки .env

| Переменная | По умолчанию в Compose | Когда менять |
|---|---|---|
| PORT | 8090 | Если порт хоста занят |
| SESSION_SECRET | Значение для локальной разработки | Задайте случайную строку перед общим доступом |
| ML_API_KEY | Локальный служебный ключ | Задайте свой общий ключ веба и ml |
| HF_TOKEN | Пусто | Для загрузки моделей pyannote |
| ASR_MODEL_NAME | large-v3-turbo | Для выбора модели Whisper |
| ASR_COMPUTE_TYPE | int8 | CPU; GPU-конфигурация принудительно задаёт float16 |
| LOCAL_LLM_URL | http://host.docker.internal:11434/v1 | Адрес локального API генерации |
| LOCAL_LLM_MODEL | qwen2.5:7b | Имя установленной модели |
| GROQ_API_KEY | Пусто | Только облачный режим |
| GEMINI_API_KEY | Пусто | Только облачный режим |
| GEMINI_GENERATION_MODELS | Пусто | Идентификатор доступной модели Gemini; обязателен для make cloud |

Значения в .env.example служат примером. Они не подтверждают доступность модели в аккаунте или качество её ответа.

## Настройки сервисов

| Переменная | В корневой сборке | Примечание |
|---|---|---|
| TRANSCRIPTION_BACKEND | demo, local или cloud | Без Compose код веба по умолчанию выбирает local |
| GENERATE_MATERIALS | false | Только строка true включает генерацию |
| SPEECH_URL | http://speech:8000 | Задан в Compose; одноимённое поле .env его не переопределяет |
| ML_URL | http://ml:8000 | Внутренний адрес ml |
| DB_PATH | /app/data/app.db | База в volume web-data |
| MAX_CONCURRENT_GENERATIONS | 1 | Одновременные задачи веба |
| ASR_LANGUAGE | ru | Язык локального распознавания |
| PARALLEL_GPU_STAGES | false | Последовательные стадии в speech |
| USE_CHECKPOINTS | false | Кеш стадий отключён в корневой сборке |
| MAX_FILE_SIZE_MB | 4000 | Лимит speech; веб отдельно ограничен 200 МБ |

Эти значения заданы в compose.yaml. Для изменения полей, которые не подставляются из .env, нужен Compose override. Полный набор переменных отдельных сервисов шире корневой сборки.
