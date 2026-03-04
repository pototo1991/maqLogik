from celery import shared_task
from django.utils import timezone
from decimal import Decimal
import logging
from .models import Maquinaria

logger = logging.getLogger('gestion')

@shared_task
def revisar_mantenimientos_proximos():
    """
    Tarea Periódica Crítica:
    Examina todas las maquinarias de todas las empresas.
    Dispara una ALERTA (vía Log o Correo en el futuro) si el valor 
    actual (Horómetro/KM) está a menos de 50 horas/km del próximo mantenimiento.
    """
    logger.info("Iniciando revisión automatizada de mantenimientos...")
    
    # Tolerancia definida por negocio = 50 horas o 50 Kilómetros
    TOLERANCIA = Decimal('50.0')
    
    maquinarias = Maquinaria.objects.all()
    alertas_generadas = 0
    
    for maquina in maquinarias:
        # Calcular diferencia
        diferencia = maquina.proximo_mantenimiento - maquina.valor_actual_medida
        
        if diferencia <= TOLERANCIA:
            msg = f"ALERTA PREVENTIVA: Máquina '{maquina.id_interno}' ({maquina.patente}) de la Empresa '{maquina.empresa.nombre_fantasia}'. Faltan solo {diferencia} {maquina.unidad_medida} para su próximo mantenimiento."
            logger.warning(msg)
            alertas_generadas += 1
            
            # TODO: Futura integración: Aquí se podría despachar un correo con send_mail() 
            # al dueño de la empresa (Usuario.roles='OWNER')

    logger.info(f"Revisión finalizada. {alertas_generadas} alertas de mantenimiento generadas frente a {maquinarias.count()} máquinas totales.")
    return alertas_generadas
