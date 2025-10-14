#!/bin/bash
set -e  # Detener ejecución si hay error

echo "Aplicando migraciones (si existen)..."
python manage.py migrate --noinput || true

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --verbosity 2

echo "Iniciando servidor Gunicorn..."
exec gunicorn gestion_qr.wsgi:application --bind 0.0.0.0:8000
