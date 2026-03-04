import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gestion.models import Maquinaria, Checklist, OrdenTrabajo, CombustibleLog, CompraCombustible, InventarioCombustible, GPSLog

print("Iniciando limpieza de base de datos operacional...")

# Borrar tablas operacionales dependientes de Maquinaria o de transacciones de combustible
GPSLog.objects.all().delete()
CombustibleLog.objects.all().delete()
Checklist.objects.all().delete()
OrdenTrabajo.objects.all().delete()
Maquinaria.objects.all().delete()

# Borrar compras de combustible externas a nombre de la empresa
CompraCombustible.objects.all().delete()

# Reiniciar inventarios a 0
InventarioCombustible.objects.all().update(stock_actual=0, precio_promedio_ponderado=0)

print("Datos Operativos Eliminados con Exito (Maquinaria, OTs, Checklists, Consumos).")
print("El Inventario de Combustible volvió a 0. Las Empresas y Usuarios se mantienen intactos.")
