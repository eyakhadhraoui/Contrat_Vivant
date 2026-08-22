# ==========================================
# Dockerfile - Backend Contrat Vivant FastAPI
# ==========================================
FROM python:3.12-slim

# Variables d'environnement Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Installation des dépendances système (Tesseract OCR, MySQL client, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    libgl1 \
    default-mysql-client \
    curl \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python avec timeout étendu
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 --retries 10 -r requirements.txt

# Copie du code source de l'application
COPY . .

# Droits d'exécution pour le script d'entrée
RUN chmod +x docker/entrypoint.sh 2>/dev/null || true

# Port exposé pour FastAPI
EXPOSE 8000

# Healthcheck de l'API
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/docs || exit 1

# Démarrage avec le script d'entrée
ENTRYPOINT ["/bin/sh", "docker/entrypoint.sh"]
