from django.urls import path
from .views import GenerarQRView

urlpatterns = [
    path('generar/', GenerarQRView.as_view(), name='generar_qr'),
]
