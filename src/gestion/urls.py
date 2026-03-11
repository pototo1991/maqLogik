from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    MaquinariaViewSet, ChecklistViewSet, GPSLogViewSet,
    OrdenTrabajoViewSet, CombustibleLogViewSet, OrdenTallerViewSet,
    MeView, MisMaquinasView, EmpresasView
)

# ─────────────────────────────────────────────────────────────
#  Router DRF — Registra automáticamente los endpoints CRUD
# ─────────────────────────────────────────────────────────────
router = DefaultRouter()
router.register(r'maquinarias', MaquinariaViewSet,    basename='maquinaria')
router.register(r'checklists',  ChecklistViewSet,     basename='checklist')
router.register(r'gps',         GPSLogViewSet,        basename='gps')
router.register(r'ordenes',     OrdenTrabajoViewSet,  basename='orden')
router.register(r'combustible', CombustibleLogViewSet, basename='combustible')
router.register(r'taller',      OrdenTallerViewSet,   basename='taller')

# ─────────────────────────────────────────────────────────────
#  Rutas manuales — Endpoints custom sin ID de objeto
# ─────────────────────────────────────────────────────────────
urlpatterns = [
    path('', include(router.urls)),

    # Perfil del usuario autenticado por JWT
    path('me/',           MeView.as_view(),       name='api-me'),

    # Máquinas asignadas al operador del token
    path('mis-maquinas/', MisMaquinasView.as_view(), name='api-mis-maquinas'),

    # Lista de empresas (solo superadmins)
    path('empresas/',     EmpresasView.as_view(),    name='api-empresas'),
]
