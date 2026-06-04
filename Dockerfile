FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Outils systeme utilises par les healthchecks Docker
RUN apt-get update \
	&& apt-get install -y --no-install-recommends wget \
	&& rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances avant le reste (cache Docker efficace)
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port
EXPOSE 62000

# Lancer uvicorn sans reload par defaut (prod). Activer avec UVICORN_RELOAD=1 en dev.
CMD ["sh", "-c", "if [ \"${UVICORN_RELOAD:-0}\" = \"1\" ]; then uvicorn main:app --host 0.0.0.0 --port ${APP_PORT:-62000} --reload; else uvicorn main:app --host 0.0.0.0 --port ${APP_PORT:-62000}; fi"]