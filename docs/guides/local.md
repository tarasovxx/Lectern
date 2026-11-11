# Локальная обработка

В локальном режиме аудио обрабатывает сервис speech. Он получает запись целиком, распознаёт речь и разделяет говорящих. Конспекты и тесты по умолчанию отключены.

## Подготовьте доступ к моделям

1. Создайте Read-токен в Hugging Face.
2. Под тем же аккаунтом примите условия [speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1) и [segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0).
3. Укажите токен в поле HF_TOKEN файла .env.

Первый запуск скачает образы; веса моделей загрузятся при первом запросе. Для работы без интернета заранее подготовьте их на целевой машине. Отправка аудио в Groq или Gemini в этом режиме отключена.

## Выберите устройство

=== "CPU"

    ```sh
    make stop
    make local
    ```

    NVIDIA GPU не требуется. Речевой контейнер закреплён на Linux x86_64. На Apple Silicon он требует эмуляции x86_64; этот вариант и его скорость пока не проверены.

=== "NVIDIA GPU"

    Нужны Linux, NVIDIA GPU, рабочий драйвер и NVIDIA Container Toolkit.

    ```sh
    nvidia-smi
    make stop
    make gpu
    ```

    В этом режиме используется CUDA-образ и вычисления float16. Диаризация и распознавание выполняются последовательно, чтобы уменьшить расход видеопамяти. Измерений LEctern на согласованном GPU пока нет.

Откройте [localhost:8090](http://localhost:8090) и загрузите запись. В /api/config поле transcription_backend должно иметь значение local.

## Подготовьте длинную запись {#long-recordings}

Веб принимает файлы до 200 МБ и читает загрузку целиком в память. Для длинного видео сначала извлеките сжатую аудиодорожку:

```sh
ffmpeg -i lesson.mp4 -vn -ac 1 -ar 16000 -b:a 64k lesson.mp3
```

У сервиса speech собственный лимит 4000 МБ. Его увеличение не меняет ограничение веб-интерфейса.

## Проверьте готовность

```sh
docker compose --profile local logs --tail=100 speech
docker compose exec speech python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())"
```

Ответ health подтверждает работу API. Модели загружаются при первом запросе, поэтому он ещё не доказывает готовность распознавания. Первый реальный файл проверяет токен, загрузку моделей и доступность устройства.
