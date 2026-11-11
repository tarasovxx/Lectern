FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /uvx /bin/
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1 UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH"
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --python /usr/local/bin/python
COPY backend ./backend
COPY public ./public
EXPOSE 8090
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8090"]
