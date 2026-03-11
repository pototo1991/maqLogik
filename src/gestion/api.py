import logging
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.utils import timezone

from .models import (
    Maquinaria, Checklist, GPSLog,
    OrdenTrabajo, CombustibleLog, OrdenTaller
)
from .serializers import (
    UsuarioSerializer, MaquinariaSerializer, ChecklistSerializer,
    GPSLogSerializer, OrdenTrabajoSerializer,
    CombustibleLogSerializer, OrdenTallerSerializer
)

logger = logging.getLogger('gestion')


# ─────────────────────────────────────────────────────────────────────────────
#  BASE: Clase Maestra Multi-Tenant para la API
# ─────────────────────────────────────────────────────────────────────────────
class TenantModelViewSet(viewsets.ModelViewSet):
    """
    Clase Maestra SaaS para la API.
    - Filtra get_queryset() por la empresa del usuario del token JWT.
    - Inyecta empresa automáticamente en perform_create().
    Esto garantiza el aislamiento de datos entre clientes del SaaS.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Sobreescribe el queryset para filtrar SIEMPRE por empresa del token.
        Evita depender del middleware de sesión web (que no aplica en JWT).
        """
        return super().get_queryset().filter(empresa=self.request.user.empresa)

    def perform_create(self, serializer):
        empresa = self.request.user.empresa
        serializer.save(empresa=empresa)


# ─────────────────────────────────────────────────────────────────────────────
#  ENDPOINT: Perfil del usuario autenticado
#  GET /api/v1/me/
# ─────────────────────────────────────────────────────────────────────────────
class MeView(APIView):
    """
    Devuelve el perfil del operador autenticado por JWT.
    Uso típico: la app móvil lo llama al iniciar para saber rol y empresa.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        logger.info(f"API:Me | Usuario {request.user.username} consultó su perfil.")
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
#  ENDPOINT: Lista de Empresas (SOLO SUPERADMINS - FLUJO MÓVIL)
#  GET /api/v1/empresas/
# ─────────────────────────────────────────────────────────────────────────────
class EmpresasView(APIView):
    """
    Lista las empresas activas. Uso exclusivo para superusuarios en la App Móvil
    para poder seleccionar a qué empresa entrar ("Ver Como").
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Solo los superusuarios pueden listar las empresas.")
            
        from .models import Empresa
        empresas = Empresa.objects.filter(activa=True).values('id', 'nombre_fantasia', 'rut_empresa')
        return Response(list(empresas))


# ─────────────────────────────────────────────────────────────────────────────
#  ENDPOINT: Máquinas asignadas al operador autenticado
#  GET /api/v1/mis-maquinas/
# ─────────────────────────────────────────────────────────────────────────────
class MisMaquinasView(APIView):
    """
    Lista únicamente las máquinas asignadas al operador del token.
    El operador sólo ve su/s máquina/s de trabajo, no toda la flota.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        maquinas = Maquinaria.objects.filter(
            operador_asignado=request.user,
            empresa=request.user.empresa
        )
        serializer = MaquinariaSerializer(maquinas, many=True)
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
#  MAQUINARIA
#  GET /api/v1/maquinarias/
# ─────────────────────────────────────────────────────────────────────────────
class MaquinariaViewSet(TenantModelViewSet):
    """Lista la flota completa de la empresa. Solo lectura para operadores."""
    queryset = Maquinaria.objects.all()
    serializer_class = MaquinariaSerializer
    http_method_names = ['get', 'head', 'options']  # Solo lectura desde móvil


# ─────────────────────────────────────────────────────────────────────────────
#  CHECKLIST
#  GET /api/v1/checklists/ | POST /api/v1/checklists/
# ─────────────────────────────────────────────────────────────────────────────
class ChecklistViewSet(TenantModelViewSet):
    """
    Permite al operador enviar el checklist diario.
    - empresa se inyecta desde el token.
    - usuario se inyecta desde el token (evita suplantación).
    """
    queryset = Checklist.objects.all()
    serializer_class = ChecklistSerializer

    def perform_create(self, serializer):
        empresa = self.request.user.empresa
        serializer.save(empresa=empresa, usuario=self.request.user)
        logger.info(
            f"API:Checklist | Usuario {self.request.user.username} "
            f"registró checklist para maquina_id={serializer.instance.maquina_id}."
        )


# ─────────────────────────────────────────────────────────────────────────────
#  GPS LOG
#  POST /api/v1/gps/
# ─────────────────────────────────────────────────────────────────────────────
class GPSLogViewSet(TenantModelViewSet):
    """
    Ruta rápida para posts automáticos de coordenadas desde el móvil.
    Solo escritura: no se consultan registros históricos por esta vía.
    """
    queryset = GPSLog.objects.all()
    serializer_class = GPSLogSerializer
    http_method_names = ['post', 'head', 'options']


# ─────────────────────────────────────────────────────────────────────────────
#  ÓRDENES DE TRABAJO
#  GET /api/v1/ordenes/ | POST /api/v1/ordenes/ | PATCH /api/v1/ordenes/{id}/cerrar/
# ─────────────────────────────────────────────────────────────────────────────
class OrdenTrabajoViewSet(TenantModelViewSet):
    """
    Gestión de Órdenes de Trabajo desde la app móvil.
    - GET: Filtra las OT del operador autenticado.
    - POST: Crea una nueva OT. El operador y empresa se inyectan automáticamente.
    - PATCH cerrar/: Registra medida_entrada y fecha_entrada para cerrar la OT.
    """
    queryset = OrdenTrabajo.objects.all()
    serializer_class = OrdenTrabajoSerializer

    def get_queryset(self):
        """El operador solo ve SUS órdenes de trabajo."""
        return OrdenTrabajo.objects.filter(
            operador=self.request.user,
            empresa=self.request.user.empresa
        )

    def perform_create(self, serializer):
        empresa = self.request.user.empresa
        serializer.save(empresa=empresa, operador=self.request.user)
        logger.info(
            f"API:OrdenTrabajo | Usuario {self.request.user.username} "
            f"creó OT #{serializer.instance.id}."
        )

    @action(detail=True, methods=['patch'], url_path='cerrar')
    def cerrar(self, request, pk=None):
        """
        Acción extra: PATCH /api/v1/ordenes/{id}/cerrar/
        Cierra la OT registrando medida_entrada y fecha_entrada actual.
        """
        orden = self.get_object()
        if orden.fecha_entrada:
            return Response(
                {'error': 'Esta Orden de Trabajo ya fue cerrada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        medida = request.data.get('medida_entrada')
        if not medida:
            return Response(
                {'error': 'Debes enviar medida_entrada para cerrar la OT.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        orden.medida_entrada = medida
        orden.fecha_entrada  = timezone.now()
        orden.save()
        logger.info(
            f"API:OrdenTrabajo | Usuario {request.user.username} "
            f"cerró OT #{orden.id} con medida_entrada={medida}."
        )
        return Response(OrdenTrabajoSerializer(orden).data)


# ─────────────────────────────────────────────────────────────────────────────
#  COMBUSTIBLE LOG
#  POST /api/v1/combustible/
# ─────────────────────────────────────────────────────────────────────────────
class CombustibleLogViewSet(TenantModelViewSet):
    """
    Registro de cargas de combustible.
    Solo POST: los registros históricos son inmutables.
    empresa y operador se inyectan desde el token.
    """
    queryset = CombustibleLog.objects.all()
    serializer_class = CombustibleLogSerializer
    http_method_names = ['post', 'head', 'options']

    def perform_create(self, serializer):
        empresa = self.request.user.empresa
        serializer.save(empresa=empresa, operador=self.request.user)
        logger.info(
            f"API:Combustible | Usuario {self.request.user.username} "
            f"registró carga de {serializer.instance.litros}L "
            f"en maquina_id={serializer.instance.maquina_id}."
        )


# ─────────────────────────────────────────────────────────────────────────────
#  ORDEN DE TALLER
#  GET /api/v1/taller/ | POST /api/v1/taller/
# ─────────────────────────────────────────────────────────────────────────────
class OrdenTallerViewSet(TenantModelViewSet):
    """
    Órdenes de mantenimiento y reparación.
    Acceso para roles MECHANIC, CHIEF y OWNER.
    empresa se inyecta desde el token.
    """
    queryset = OrdenTaller.objects.all()
    serializer_class = OrdenTallerSerializer
    ROLES_PERMITIDOS = {'MECHANIC', 'CHIEF', 'OWNER'}

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user.rol not in self.ROLES_PERMITIDOS:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "No tienes permiso para acceder al módulo de Taller. "
                "Se requiere rol MECHANIC, CHIEF u OWNER."
            )
