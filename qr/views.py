from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import qrcode
import io
from django.http import HttpResponse
import requests
from django.conf import settings

INVENTARIO_API = settings.INVENTARIO_API.rstrip("/")  # asegurar sin slash final

class GenerarQRView(APIView):
    def post(self, request):
        codigo = request.data.get("codigo")
        if not codigo:
            return Response({"error": "Debe enviar un código alfanumérico"}, status=status.HTTP_400_BAD_REQUEST)

        # Buscar por código en Inventario (no por ID)
        resp = requests.get(f"{INVENTARIO_API}/?codigo={codigo}")
        if resp.status_code == 200:
            data = resp.json()
            if not data:  # lista vacía
                crear = requests.post(f"{INVENTARIO_API}/", json={"codigo": codigo})
                if crear.status_code not in [200, 201]:
                    return Response({"error": "No se pudo crear en inventario"}, status=crear.status_code)
        else:
            # Si el GET falla, intentar crear directamente
            crear = requests.post(f"{INVENTARIO_API}/", json={"codigo": codigo})
            if crear.status_code not in [200, 201]:
                return Response({"error": "No se pudo crear en inventario"}, status=crear.status_code)

        # Generar QR en memoria
        qr_img = qrcode.make(codigo)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(buffer.getvalue(), content_type="image/png")
