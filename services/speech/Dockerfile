FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PARALLEL_GPU_STAGES=false HF_HOME=/models
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-runtime.txt constraints-torch.txt ./
RUN pip install --no-cache-dir torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -c constraints-torch.txt -r requirements-runtime.txt
COPY app ./app
COPY configs ./configs
RUN useradd --create-home speech && mkdir -p /models /app/data && chown -R speech:speech /models /app/data
USER speech
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
