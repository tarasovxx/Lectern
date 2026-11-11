# Проверки первой сборки

11 ноября 2026, macOS ARM64, Python 3.14. Тестовое окружение размещено вне репозитория. Контейнеры настроены на Python 3.11; GPU-образ использует Python 3.10.

| Команда | Результат |
|---|---|
| python scripts/test.py | Web: 15, ML: 33, speech: 55 тестов прошли; всего 103 |
| python scripts/smoke.py | PASS: demo page → upload → completed → transcript/analytics → delete → 404 |
| docker compose --profile local --profile materials config --quiet | Код возврата 0 |
| docker compose -f compose.yaml -f compose.gpu.yaml --profile local config --quiet | Код возврата 0 |
| docker compose -f compose.yaml -f compose.cloud.yaml --profile materials config --quiet | Код возврата 0 с тестовыми значениями обязательных ключей |
| node --check services/web/public/teacher/script.js | Код возврата 0 |

HTTP-проверка выполнялась против локального Uvicorn, в режиме demo. Внешние модели и сервисы не вызывались. Предупреждения устаревания в зависимостях FastAPI/Starlette на Python 3.14 сохранились.

Сборка образов Docker, реальные запросы к Groq/Gemini/Ollama, распознавание записи, скорость и F1 не проверены. Docker-сервер на машине не запущен. CI содержит проверку сборки web/ml и HTTP-сценария демо; его результат нужно смотреть отдельно после push.
