import qrcode, io, requests
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

INVENTARIO_API = settings.INVENTARIO_API.rstrip("/")

class GenerarQRView(APIView):
    def post(self, request):
        codigo = request.data.get("codigo")
        if not codigo:
            return Response({"error": "Debe enviar un código alfanumérico"}, status=400)

        try:
            # Verifica si ya existe el código
            resp = requests.get(f"{INVENTARIO_API}/?codigo={codigo}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if not data:
                    # Si no existe, lo crea
                    crear = requests.post(f"{INVENTARIO_API}/", json={"codigo": codigo}, timeout=10)
                    if crear.status_code not in [200, 201]:
                        return Response({"error": f"No se pudo crear ({crear.status_code})"}, status=crear.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        # Genera el QR
        qr_img = qrcode.make(codigo)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(buffer.getvalue(), content_type="image/png")
