# Este archivo se asegura de que la app celery siempre sea importada
# cuando Django inicia, para que la anotación @shared_task funcione.
from .celery import app as celery_app

__all__ = ('celery_app',)
