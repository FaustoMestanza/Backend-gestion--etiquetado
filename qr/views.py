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


INVENTARIO_API = settings.INVENTARIO_API.rstrip("/")
AUTH_TOKEN = getattr(settings, "AUTH_TOKEN", None)


@method_decorator(csrf_exempt, name='dispatch')
class GenerarQRView(APIView):
    """
    Genera un código QR y registra el equipo en el microservicio de Inventario.
    """

    def post(self, request, *args, **kwargs):
        codigo = request.data.get("codigo")
        if not codigo:
            return Response({"error": "Debe enviar un código alfanumérico"}, status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Cabeceras con autenticación
        headers = {"Content-Type": "application/json"}
        if AUTH_TOKEN:
            headers["Authorization"] = f"Bearer {AUTH_TOKEN}"  # Token de Inventario

        # 🔹 Verificar existencia del equipo
        try:
            check = requests.get(f"{INVENTARIO_API}/?codigo={codigo}", headers=headers, timeout=10)
        except Exception as e:
            return Response({"error": f"Error de conexión con Inventario: {str(e)}"}, status=500)

        if check.status_code == 401:
            return Response({"error": "Token inválido o expirado. Regenera el AUTH_TOKEN en Azure."}, status=401)

        # 🔹 Si no existe, crear el equipo con los campos requeridos
        if check.status_code == 200:
            data = check.json()
            if not data:
                crear = requests.post(
                    f"{INVENTARIO_API}/",
                    json={
                        "codigo": codigo,
                        "nombre": f"Equipo {codigo}",
                        "categoria": "General",
                        "descripcion": "Equipo registrado automáticamente desde el microservicio QR",
                        "ubicacion": "Bodega Principal",
                        "estado": "Disponible"
                    },
                    headers=headers,
                    timeout=10
                )
                if crear.status_code not in [200, 201]:
                    return Response({
                        "error": f"No se pudo crear en inventario. Código: {crear.status_code}, Respuesta: {crear.text}"
                    }, status=crear.status_code)
        elif check.status_code == 404:
            crear = requests.post(
                f"{INVENTARIO_API}/",
                json={
                    "codigo": codigo,
                    "nombre": f"Equipo {codigo}",
                    "categoria": "General",
                    "descripcion": "Equipo registrado automáticamente desde el microservicio QR",
                    "ubicacion": "Bodega Principal",
                    "estado": "Disponible"
                },
                headers=headers,
                timeout=10
            )
            if crear.status_code not in [200, 201]:
                return Response({
                    "error": f"No se pudo crear en inventario. Código: {crear.status_code}, Respuesta: {crear.text}"
                }, status=crear.status_code)
        else:
            return Response({
                "error": f"Respuesta inesperada del Inventario: {check.status_code} - {check.text}"
            }, status=check.status_code)

        # 🔹 Generar el código QR
        qr_img = qrcode.make(codigo)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(buffer.getvalue(), content_type="image/png")
