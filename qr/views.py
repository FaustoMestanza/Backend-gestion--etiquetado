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


@method_decorator(csrf_exempt, name='dispatch')
class GenerarQRView(APIView):
    """
    Genera un código QR y crea el registro en el microservicio de Inventario si no existe.
    """

    def post(self, request, *args, **kwargs):
        # 🔹 Asegurar lectura correcta del JSON
        try:
            codigo = request.data.get("codigo")
        except Exception:
            return Response({"error": "Formato JSON inválido"}, status=status.HTTP_400_BAD_REQUEST)

        if not codigo:
            return Response({"error": "Debe enviar un código alfanumérico"}, status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Buscar si ya existe en el Inventario
        try:
            resp = requests.get(f"{INVENTARIO_API}/?codigo={codigo}")
        except Exception as e:
            return Response({"error": f"Error al conectar con Inventario: {str(e)}"}, status=500)

        if resp.status_code == 200:
            data = resp.json()
            if not data:  # si no existe, crear
                crear = requests.post(f"{INVENTARIO_API}/", json={"codigo": codigo})
                if crear.status_code not in [200, 201]:
                    return Response({"error": "No se pudo crear en inventario"}, status=crear.status_code)
        else:
            # si la API no responde 200, intenta crear de todos modos
            crear = requests.post(f"{INVENTARIO_API}/", json={"codigo": codigo})
            if crear.status_code not in [200, 201]:
                return Response({"error": "No se pudo crear en inventario"}, status=crear.status_code)

        # 🔹 Generar QR en memoria
        qr_img = qrcode.make(codigo)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(buffer.getvalue(), content_type="image/png")
