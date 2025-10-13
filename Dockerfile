# Imagen base oficial de Python
FROM python:3.12-slim

# Establecer directorio de trabajo
WORKDIR /app

# Evitar archivos .pyc y mejorar salida de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .



CMD python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 gestion_qr.wsgi
