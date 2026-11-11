# yadrovichi

## Что делаем

Локальный сервис: аудио или видео урока → текст, разбитый по ролям и таймкодам,
плюс аналитика вовлечённости. Кто говорил, когда и что сказал. Всё на своём
железе, без облака; в интерфейсе реплики идут вживую по мере распознавания.

## Пайплайн

1. **Диаризация** — pyannote (`speaker-diarization-community-1`) по всему файлу
   целиком → сегменты со спикерами. Аудио читаем через soundfile в обход
   torchcodec.
2. **Транскрибация** — faster-whisper large-v3-turbo (`float16`) → слова с
   таймкодами и уверенностью (`probability`).
3. **Склейка** — слова к спикерам по перекрытию, реплики, сглаживание коротких
   ложных переключений `A→B→A`.
4. **Роли** — преподаватель по графу переходов + ученик 1, 2, 3… (граф-первично).
5. **Формулы** — `mathnorm`: речь формул → символьный вид для LLM (подключён и в
   батче, и в стриминге; поля `llm_text`/`has_math`).
6. **Постобработка** — словарь замен ошибок ASR + батч-достройка реплик (филлеры,
   повторы, регистр) пачками по ~10 реплик.
7. **Выдача** — FastAPI + Gradio: батчем или потоком по мере готовности.

Вход — и аудио, и видео: из видео ffmpeg вытягивает звуковую дорожку, дальше
распознавание то же. Стадии на GPU идут **последовательно**, pyannote снимается
с карты перед whisper (устойчивость к OOM на общей карте).

## Результаты (RTF)

| Файл | Длительность | RTF пайплайна | Обработка |
|---|---|---|---|
| Семинар (аудио) | 30 мин | 0.062 | 1 мин 52 с |
| Семинар B214 (аудио) | 1 ч 16 мин | 0.051 | 3 мин 53 с |
| Лекция ML System Design (видео) | 1 ч 24 мин | 0.103 | 8 мин 41 с |
| Урок STEM (видео) | 1 ч 31 мин | 0.127 | 11 мин 34 с |

Разбор нелинейности — в [docs/performance.md](docs/performance.md).

## Достижения в цифрах

- **RTF 0.051–0.127** на 4 файлах (30 мин – 1.5 ч) — кратно под бюджетом **0.4**.
- Полуторачасовое видео обрабатывается за **11 мин 34 с**.
- RTF определяет **плотность речи**, а не длина: длинный семинар (1 ч 16 мин,
  0.051) быстрее по RTF короткого (30 мин, 0.062).
- **4 спикера**, роли граф-первично; на лекции ML System Design аналитика ловит
  кейс «докладчик-студент 89% времени, преподаватель 3.5%».
- Устойчивость к **0 OOM** на общей карте (offload pyannote + один воркер).
- Расхождение нашей транскрипции со встроенной ASR Контур Толк — **~33%**,
  качественно в нашу пользу (см. [docs/wer.md](docs/wer.md)).
- **55 юнит-тестов** без загрузки моделей.

## Фичи интерфейса (`/ui`)

- **Живой стриминг** — реплики по ролям появляются по мере распознавания.
- **Цветная лента спикеров** над расшифровкой — каждая реплика отрезком своего
  цвета (совпадает с текстом).
- **Аналитика вовлечённости** — доли речи по спикерам, преподаватель vs ученики,
  интерактивность (переключений/мин), график вовлечённости по времени, флаги
  («урок ведёт ученик», «один ученик доминирует» …).
- **Подсветка неуверенных слов** — слова с уверенностью ASR < 0.5 подчёркнуты.
- **Экспорт** — JSON, SRT, VTT, TXT, DOCX (расшифровка по ролям) одним блоком.
- **Поиск** по расшифровке + **фильтр по спикеру** (список заполняется реальными
  спикерами именно этого файла после прогона).
- **Правки словаря** замен ошибок ASR прямо из интерфейса.
- **История прогонов** (на диске) — вернуться к прошлым результатам.
- **Светлая/тёмная тема**, чекпоинты (кеш стадий + потоковая запись на диск).

## Железо

Целевой сервер — RTX A4000 (Ampere, sm_86, 16 ГБ VRAM, CUDA 13.x). Куратор
заявлял GTX 1080, по факту A4000 → `compute_type=float16`, не int8.

## Установка

Команды выполняются из `services/speech`. Нужен uv 0.13.6 и Python 3.10–3.12.
Для распознавания поддерживается Linux x86_64 с glibc ≥ 2.28, ffmpeg и
libsndfile. Веса pyannote требуют HF_TOKEN и принятия условий модели.

Для API и тестов достаточно базовых зависимостей. Torch, pyannote и Whisper
устанавливаются только с одним из дополнений: `cpu` или `cuda` (CUDA 12.8).
Они несовместимы друг с другом. Gradio подключается дополнением `ui`, jiwer —
дополнением `metrics`. При каждом `uv run` указывайте нужные дополнения:
uv синхронизирует окружение перед запуском.

```bash
# Тесты без моделей, в том числе на macOS
uv sync --locked --group dev
uv run --locked --group dev python -m pytest tests -q

# На сервере с NVIDIA GPU
uv sync --locked --no-dev --extra cuda --python 3.10
cp .env.example .env      # вписать HF_TOKEN
uv run --locked --no-dev --extra cuda python -c "import torch; print(torch.cuda.get_device_capability(0))"

# На Linux без GPU
uv sync --locked --no-dev --extra cpu --python 3.11
```

## Запуск

```bash
# Прогон пайплайна на файле → JSON с таймлайном, ролями и RTF
uv run --locked --no-dev --extra cuda python -m scripts.smoke data/lesson.mp4

# Сервис: /docs — API, /ui — интерфейс. Один воркер: видеокарта одна.
PARALLEL_GPU_STAGES=false uv run --locked --no-dev --extra cuda --extra ui \
    uvicorn app.main:app --workers 1 --port 8000

# Аналитика вовлечённости по готовому результату (без GPU)
uv run --locked --no-dev python -m scripts.analyze artifacts/ml_result.json --output artifacts/analytics.json

# WER: против человеческого эталона (аудио + субтитры) и расхождение с Толком
uv run --locked --no-dev --extra cuda --extra metrics python -m scripts.compute_wer \
    --audio data/lecture.m4a --reference data/lecture.ru.srt
uv run --locked --no-dev --extra metrics python -m scripts.wer_vs_talk \
    --ours artifacts/ml_result.json --talk "Транскрибация толк.docx"

# Юнит-тесты (без GPU)
uv run --locked --group dev python -m pytest tests -q
```

Для CPU замените `--extra cuda` на `--extra cpu`. Контейнеры используют тот же
lock: Dockerfile — Python 3.11 и CPU, Dockerfile.gpu — Python 3.10 и CUDA 12.8.
Оба образа собираются для `linux/amd64`; Gradio и метрики в них не включены.

```bash
docker build --platform linux/amd64 -t lectern-speech:cpu .
docker build --platform linux/amd64 -f Dockerfile.gpu -t lectern-speech:cuda .
```

## Рабочий процесс на сервере (деплой)

Один воркер, видеокарта одна и общая. Типовые команды:

```bash
# 1. Залить файл на сервер — в белом окне ПК (где C:\), НЕ внутри ssh
scp "C:\путь\запись.mp4" yadrovic@<сервер>:~/yadrovichi/data/lesson.mp4

# 2. Обновить код и перезапустить сервис — на сервере
pkill -u yadrovic -f uvicorn
cd ~/yadrovichi && git pull
PARALLEL_GPU_STAGES=false nohup uv run --locked --no-dev --extra cuda --extra ui \
    uvicorn app.main:app --workers 1 --port 8000 \
    > ~/uvicorn.log 2>&1 & sleep 4 && tail -5 ~/uvicorn.log   # ждём Application startup complete

# 3. Открыть интерфейс с ПК — проброс порта в отдельном окне (не закрывать)
ssh -L 8000:localhost:8000 yadrovic@<сервер>     # затем http://localhost:8000/ui

# Если карту занял чужой процесс (OOM) — посмотреть, кто держит память
nvidia-smi
```

## Ручки API

- `POST /stream` — потоковая выдача NDJSON: meta → реплики по мере готовности → done
- `POST /transcribe` — батч, весь результат одним JSON
- `GET /analytics/{job_id}` — аналитика вовлечённости по сохранённому результату
- `GET /export/{job_id}?format=srt|vtt|txt|docx` — экспорт расшифровки
- `GET /ui` — Gradio-интерфейс

## Структура

| Файл | Что делает |
|---|---|
| `app/core/config.py` | настройки из `.env` (модели, устройство, лимит файла) |
| `app/services/audio.py` | нормализация аудио и длительность (ffmpeg) |
| `app/services/asr.py` | faster-whisper, ленивая загрузка, RTF, уверенность слов |
| `app/services/diarization.py` | pyannote (soundfile в обход torchcodec) + offload |
| `app/services/alignment.py` | привязка слов, реплики, сглаживание переключений |
| `app/services/role_detection.py` | преподаватель по графу + маркерам |
| `app/services/mathnorm.py` | формулы речью → символьный вид для LLM |
| `app/services/text_postprocessing.py` | словарь замен ошибок ASR (+ пользовательский) |
| `app/services/refine.py` | батч-достройка реплик (филлеры, повторы, регистр) |
| `app/services/analytics.py` | вовлечённость: доли речи, интерактивность, лента |
| `app/services/export_subs.py` | экспорт в SRT/VTT |
| `app/services/export_transcript.py` | экспорт по ролям в TXT/DOCX |
| `app/services/user_dict.py` | пользовательские правки словаря замен |
| `app/services/checkpoint.py` | кеш стадий + потоковая запись реплик |
| `app/services/pipeline.py` | батч-оркестратор: диаризация → ASR → склейка → роли |
| `app/services/streaming.py` | потоковый пайплайн: граф-роли → потоковый ASR |
| `app/main.py` | FastAPI: `/stream`, `/transcribe`, `/analytics`, `/export` |
| `app/ui.py` | Gradio `/ui`: лента, аналитика, поиск/фильтр, экспорт, тема |
| `configs/` | словари маркеров преподавателя и замен ошибок ASR |
| `scripts/smoke.py` | прогон пайплайна на файле |
| `scripts/analyze.py` | аналитика вовлечённости по готовому JSON |
| `scripts/compute_wer.py` | WER против эталонных субтитров |
| `scripts/wer_vs_talk.py` | расхождение нашей транскрипции с транскриптом Толк |
| `tests/` | юнит-тесты (alignment, роли, mathnorm, аналитика, refine, экспорт, словарь) |

## Договорённости

- Кластеризация **одна на весь файл**, не почанково; `min_speakers=2`, верх не задаём
- Аудио, видео и `.env` в гит не коммитить
- `compute_type=float16` (Ampere), не int8
- Стадии гоняем **последовательно** (`PARALLEL_GPU_STAGES=false`) + offload pyannote
- Лимит размера файла — `MAX_FILE_SIZE_MB` в `.env` (по умолчанию 4 ГБ, под видео)
- DER не заявляем: эталона с таймкодами нет. WER подаём как расхождение с Толком
  (не как абсолютную точность) — детали в [docs/wer.md](docs/wer.md)

## Открытые задачи

Из роадмапа закрыты все **P0** и **P1**; из **P2** сделаны экспорт txt/docx,
поиск, фильтр по спикеру, правки словаря. Осталось:

- **P2 · Клик по реплике → перемотка** — не сделано (по решению команды).
- **LLM-достройка** неуверенных реплик — движок `refine` оставлен под замену
  (сейчас правила: филлеры, повторы, регистр).
- **Точность против человека** — нужен ручной эталон 5 мин для accuracy-WER
  (текущее число — расхождение с Толком ~33%, не абсолютная точность).
- Не по коду: презентация (продакт), драйверная гигиена (после защиты).
