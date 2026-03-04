from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import MaquinariaViewSet, ChecklistViewSet, GPSLogViewSet

router = DefaultRouter()
router.register(r'maquinarias', MaquinariaViewSet, basename='maquinaria')
router.register(r'checklists', ChecklistViewSet, basename='checklist')
router.register(r'gps', GPSLogViewSet, basename='gps')

urlpatterns = [
    path('', include(router.urls)),
]
