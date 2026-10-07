# EduRisk Predictor — production image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_CONFIG=production

WORKDIR /srv/app

# System deps (matplotlib/fontconfig)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6 libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

COPY . .

RUN mkdir -p data/uploads data/raw artifacts/plots

EXPOSE 8000

# Bootstrap: create directories, generate dataset if absent, train if absent.
RUN python -m scripts.setup --skip-seed

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "wsgi:app"]
