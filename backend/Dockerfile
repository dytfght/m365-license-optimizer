# ============================================
# M365 License Optimizer - Backend Dockerfile
# FastAPI + PostgreSQL + Redis
# ============================================

FROM python:3.12-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système (y compris build-essential pour hiredis)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Nettoyer les build tools pour réduire la taille de l'image
RUN apt-get purge -y --auto-remove build-essential

# Copier le code source
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini .

# Créer un utilisateur non-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Port exposé
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)" || exit 1

# Commande de démarrage
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
