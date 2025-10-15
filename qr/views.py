import qrcode, io, requests, traceback
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

INVENTARIO_API = settings.INVENTARIO_API.rstrip("/")

class GenerarQRView(APIView):
    """
    Vista de depuración: genera el QR y muestra detalles del error si algo falla.
    """

    def post(self, request):
        codigo = request.data.get("codigo")
        if not codigo:
            return Response({"error": "Debe enviar un código alfanumérico"}, status=400)

        try:
            # --- PRUEBA DE CONEXIÓN AL INVENTARIO ---
            check_url = f"{INVENTARIO_API}/?codigo={codigo}"
            check = requests.get(check_url, timeout=30)

            # --- LOG DE ESTADO ---
            print(f"[DEBUG] Verificando {check_url} -> {check.status_code}")

            # Si no existe, crear
            if check.status_code == 404 or not check.json():
                crear_url = f"{INVENTARIO_API}/"
                crear_data = {"codigo": codigo}
                crear = requests.post(crear_url, json=crear_data, timeout=30)

                print(f"[DEBUG] Creando {crear_url} -> {crear.status_code}")

                if crear.status_code not in [200, 201]:
                    return Response({
                        "error": "No se pudo crear el equipo en Inventario",
                        "codigo_http": crear.status_code,
                        "detalle": crear.text,
                        "endpoint": crear_url,
                        "enviado": crear_data
                    }, status=crear.status_code)

        except requests.exceptions.Timeout:
            return Response({
                "error": "Timeout — el microservicio Inventario no respondió a tiempo",
                "endpoint": INVENTARIO_API
            }, status=504)

        except requests.exceptions.ConnectionError as e:
            return Response({
                "error": "No se pudo conectar con el microservicio Inventario",
                "detalle": str(e),
                "endpoint": INVENTARIO_API
            }, status=503)

        except Exception as e:
            tb = traceback.format_exc()
            return Response({
                "error": "Error inesperado",
                "detalle": str(e),
                "traceback": tb
            }, status=500)

        # --- GENERAR QR ---
        try:
            qr_img = qrcode.make(codigo)
            buffer = io.BytesIO()
            qr_img.save(buffer, format="PNG")
            buffer.seek(0)
            return HttpResponse(buffer.getvalue(), content_type="image/png")

        except Exception as e:
            tb = traceback.format_exc()
            return Response({
                "error": "Error generando el QR",
                "detalle": str(e),
                "traceback": tb
            }, status=500)
