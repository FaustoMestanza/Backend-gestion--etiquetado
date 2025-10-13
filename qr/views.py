from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import qrcode
import io
from django.http import HttpResponse
import requests
from django.conf import settings


INVENTARIO_API = settings.INVENTARIO_API

class GenerarQRView(APIView):
    def post(self, request):
        codigo = request.data.get("codigo")
        if not codigo:
            return Response({"error": "Debe enviar un código alfanumérico"}, status=status.HTTP_400_BAD_REQUEST)

        # Consultar si existe en Inventario
        resp = requests.get(f"{INVENTARIO_API}{codigo}/")
        if resp.status_code == 404:
            # Crear registro vacío
            crear = requests.post(INVENTARIO_API, json={"codigo": codigo})
            if crear.status_code not in [200, 201]:
                return Response({"error": "No se pudo crear en inventario"}, status=crear.status_code)

        # Generar QR en memoria
        qr_img = qrcode.make(codigo)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        # Enviar imagen como respuesta
        return HttpResponse(buffer.getvalue(), content_type="image/png")
