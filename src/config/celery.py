import os
from celery import Celery

# Establecer el módulo de settings de Django por defecto para el programa principal 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('maqlogik')

# Usar una cadena aquí significa que el worker no tiene que serializar
# el objeto de configuración en los procesos hijos.
# - namespace='CELERY' significa que todas las claves de configuración de celery
#   deben tener el prefijo `CELERY_`.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar módulos de tareas de todas las aplicaciones registradas de Django.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
