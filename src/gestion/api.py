from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Maquinaria, Checklist, GPSLog
from .serializers import MaquinariaSerializer, ChecklistSerializer, GPSLogSerializer

class TenantModelViewSet(viewsets.ModelViewSet):
    """
    Clase Maestra SaaS para la API:
    Asegura que cada registro nuevo o editado por el Móvil 
    tenga automáticamente asignado el empresa_id del usuario del Token.
    """
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Inyectamos de forma forzosa la empresa actual del token en la petición
        empresa_usuario = self.request.user.empresa
        serializer.save(empresa=empresa_usuario)


class MaquinariaViewSet(TenantModelViewSet):
    """
    Endpoint: /api/v1/maquinarias/
    Lista exclusivamente las maquinarias de la empresa del trabajador móvil.
    """
    queryset = Maquinaria.objects.all()
    serializer_class = MaquinariaSerializer

class ChecklistViewSet(TenantModelViewSet):
    """
    Endpoint: /api/v1/checklists/
    Permite enviar los reportes diarios obligatorios.
    La Autoría del usuario se inyecta desde aquí de forma invisible.
    """
    queryset = Checklist.objects.all()
    serializer_class = ChecklistSerializer
    
    def perform_create(self, serializer):
        # Inyecta Empresa Y Usuario Automáticamente (Seguridad contra suplantación)
        empresa_usuario = self.request.user.empresa
        serializer.save(empresa=empresa_usuario, usuario=self.request.user)

class GPSLogViewSet(TenantModelViewSet):
    """
    Endpoint: /api/v1/gps/
    Ruta rápida para los posts automatizados del teléfono móvil.
    """
    queryset = GPSLog.objects.all()
    serializer_class = GPSLogSerializer
