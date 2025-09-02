# Stage 1: Build stage
FROM python:3.10.7-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final stage
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app/wheels /wheels
COPY . .

RUN pip install --no-index --find-links=/wheels /wheels/*

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 8000

CMD ["gunicorn", "eye2_project.wsgi:application", "--bind", "0.0.0.0:8000"]
