from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CompraCombustible, CombustibleLog, InventarioCombustible
from decimal import Decimal

import logging
logger = logging.getLogger('gestion')

@receiver(post_save, sender=CompraCombustible)
def actualizar_inventario_por_compra(sender, instance, created, **kwargs):
    """
    Automatización Financiera:
    Cuando una Empresa compra combustible para su tanque interno, 
    suma los litros al inventario y recalcula matemáticamente
    el Precio Promedio Ponderado.
    """
    if created:
        empresa = instance.empresa
        
        # Obtenemos o creamos el registro de inventario para el Cliente SaaS
        inventario, created = InventarioCombustible.objects.get_or_create(empresa=empresa)
        
        stock_anterior = inventario.stock_actual
        precio_anterior = inventario.precio_promedio_ponderado
        
        nuevos_litros = instance.cantidad_litros
        nuevo_precio = instance.precio_litro
        
        # Fórmula Precio Ponderado = ((Stock Anterior * Precio Anterior) + (Nuevos Litros * Nuevo Precio)) / Total Litros
        valor_inventario_anterior = stock_anterior * precio_anterior
        valor_nueva_compra = nuevos_litros * nuevo_precio
        
        nuevo_stock_total = stock_anterior + nuevos_litros
        
        if nuevo_stock_total > 0:
            nuevo_precio_ponderado = (valor_inventario_anterior + valor_nueva_compra) / nuevo_stock_total
        else:
            nuevo_precio_ponderado = Decimal('0.00')
            
        inventario.stock_actual = nuevo_stock_total
        inventario.precio_promedio_ponderado = round(nuevo_precio_ponderado, 2)
        inventario.save()
        
        logger.info(f"Inventario COMBUSTIBLE Actualizado [COMPRA] para {empresa.nombre_fantasia}: +{nuevos_litros}L a ${nuevo_precio_ponderado}/L")

@receiver(post_save, sender=CombustibleLog)
def actualizar_inventario_por_carga_maquina(sender, instance, created, **kwargs):
    """
    Regla Operativa:
    (Movido a la vista views.py para poder interactuar con los mensajes de error de recarga y fallas de stock) 
    """
    pass
