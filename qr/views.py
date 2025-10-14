from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import qrcode
import io
from django.http import HttpResponse
import requests
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


INVENTARIO_API = settings.INVENTARIO_API.rstrip("/")
AUTH_TOKEN = getattr(settings, "AUTH_TOKEN", None)  # 🔹 Lee la variable del entorno Azure


@method_decorator(csrf_exempt, name='dispatch')
class GenerarQRView(APIView):
    """
    Genera un código QR y crea el registro en el microservicio de Inventario si no existe.
    """

    def post(self, request, *args, **kwargs):
        # 🔹 Leer el JSON correctamente
        try:
            codigo = request.data.get("codigo")
        except Exception:
            return Response({"error": "Formato JSON inválido"}, status=status.HTTP_400_BAD_REQUEST)

        if not codigo:
            return Response({"error": "Debe enviar un código alfanumérico"}, status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Headers con autenticación JWT
        headers = {
            "Content-Type": "application/json",
        }

        if AUTH_TOKEN:
            headers["Authorization"] = f"Bearer {AUTH_TOKEN}"

        # 🔹 Consultar si existe en Inventario
        try:
            resp = requests.get(f"{INVENTARIO_API}/?codigo={codigo}", headers=headers, timeout=10)
        except Exception as e:
            return Response({"error": f"Error al conectar con Inventario: {str(e)}"}, status=500)

        # 🔹 Crear si no existe
        if resp.status_code == 200:
            data = resp.json()
            if not data:
                crear = requests.post(f"{INVENTARIO_API}/", json={"codigo": codigo}, headers=headers, timeout=10)
                if crear.status_code not in [200, 201]:
                    return Response({"error": "No se pudo crear en inventario"}, status=crear.status_code)
        elif resp.status_code in [401, 403]:
            return Response({"error": "Token inválido o expirado al conectar con Inventario"}, status=resp.status_code)
        else:
            crear = requests.post(f"{INVENTARIO_API}/", json={"codigo": codigo}, headers=headers, timeout=10)
            if crear.status_code not in [200, 201]:
                return Response({"error": "No se pudo crear en inventario"}, status=crear.status_code)

        # 🔹 Generar QR
        qr_img = qrcode.make(codigo)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(buffer.getvalue(), content_type="image/png")
