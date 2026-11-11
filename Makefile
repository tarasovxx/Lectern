SHELL := /bin/sh
.PHONY: demo local gpu materials gpu-materials cloud stop logs config test docs docs-build sync lock lock-check

demo:
	TRANSCRIPTION_BACKEND=demo GENERATE_MATERIALS=false docker compose up -d --build web
local:
	TRANSCRIPTION_BACKEND=local GENERATE_MATERIALS=false docker compose --profile local up -d --build
# NVIDIA GPU on Linux with NVIDIA Container Toolkit.
gpu:
	TRANSCRIPTION_BACKEND=local GENERATE_MATERIALS=false docker compose -f compose.yaml -f compose.gpu.yaml --profile local up -d --build
materials:
	TRANSCRIPTION_BACKEND=local GENERATE_MATERIALS=true docker compose --profile local --profile materials up -d --build
gpu-materials:
	TRANSCRIPTION_BACKEND=local GENERATE_MATERIALS=true docker compose -f compose.yaml -f compose.gpu.yaml -f compose.ollama.yaml --profile local --profile materials --profile ollama up -d --build
cloud:
	docker compose -f compose.yaml -f compose.cloud.yaml --profile materials up -d --build
stop:
	docker compose -f compose.yaml -f compose.ollama.yaml --profile local --profile materials --profile ollama down
logs:
	docker compose -f compose.yaml -f compose.ollama.yaml --profile local --profile materials --profile ollama logs -f --tail=100
config:
	docker compose --profile local --profile materials config --quiet
test:
	uv run --locked python scripts/test.py

# Documentation dependencies are selected from the docs group.
docs:
	uv run --locked --group docs mkdocs serve --dev-addr 127.0.0.1:8001
docs-build:
	uv run --locked --group docs mkdocs build --strict

sync:
	uv sync --locked
lock:
	uv lock
	uv lock --project services/web
	uv lock --project services/ml
	uv lock --project services/speech
lock-check:
	uv lock --check
	uv lock --check --project services/web
	uv lock --check --project services/ml
	uv lock --check --project services/speech
