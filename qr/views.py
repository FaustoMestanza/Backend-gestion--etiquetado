import qrcode
import io
import base64
import requests
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from django.conf import settings

INVENTARIO_API = settings.INVENTARIO_API.rstrip("/")


class GenerarQRView(APIView):
    """
    Genera un código QR y registra el equipo en el microservicio de Inventario.
    No usa autenticación ni validación previa.
    """

    def post(self, request):
        codigo = request.data.get("codigo")
        if not codigo:
            return JsonResponse(
                {"error": "Debe enviar un código alfanumérico"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 🔹 Crear directamente el equipo en Inventario
            crear = requests.post(
                f"{INVENTARIO_API}/",
                json={"codigo": codigo},
                timeout=15
            )

            if crear.status_code in [200, 201]:
                estado = "registrado"
            elif crear.status_code == 400:
                estado = "ya existe"
            else:
                return JsonResponse(
                    {
                        "error": "No se pudo registrar en Inventario",
                        "codigo_http": crear.status_code,
                        "detalle": crear.text
                    },
                    status=crear.status_code
                )

            # 🔹 Generar QR en memoria (sin format="PNG")
            qr_img = qrcode.make(codigo)
            buffer = io.BytesIO()
            qr_img.save(buffer)
            buffer.seek(0)

            # 🔹 Convertir QR a base64 (para Postman o Flutter)
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # 🔹 Respuesta JSON
            return JsonResponse(
                {
                    "mensaje": f"Equipo '{codigo}' {estado} correctamente en Inventario.",
                    "codigo": codigo,
                    "qr_base64": qr_base64
                },
                status=status.HTTP_201_CREATED
            )

        except requests.exceptions.Timeout:
            return JsonResponse(
                {"error": "El microservicio de Inventario no respondió a tiempo."},
                status=504
            )
        except requests.exceptions.ConnectionError:
            return JsonResponse(
                {"error": "No se pudo conectar con el microservicio de Inventario."},
                status=503
            )
        except Exception as e:
            return JsonResponse(
                {"error": f"Error inesperado: {str(e)}"},
                status=500
            )
