SHELL := /bin/sh
.PHONY: demo local gpu materials cloud stop logs config test

demo:
	TRANSCRIPTION_BACKEND=demo GENERATE_MATERIALS=false docker compose up -d --build web
local:
	TRANSCRIPTION_BACKEND=local GENERATE_MATERIALS=false docker compose --profile local up -d --build
# NVIDIA GPU on Linux with NVIDIA Container Toolkit.
gpu:
	TRANSCRIPTION_BACKEND=local GENERATE_MATERIALS=false docker compose -f compose.yaml -f compose.gpu.yaml --profile local up -d --build
materials:
	TRANSCRIPTION_BACKEND=local GENERATE_MATERIALS=true docker compose --profile local --profile materials up -d --build
cloud:
	docker compose -f compose.yaml -f compose.cloud.yaml --profile materials up -d --build
stop:
	docker compose --profile local --profile materials down
logs:
	docker compose --profile local --profile materials logs -f --tail=100
config:
	docker compose --profile local --profile materials config --quiet
test:
	python3 scripts/test.py
