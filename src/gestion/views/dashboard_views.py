from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.utils import timezone
from datetime import timedelta
from ..models import Maquinaria, Checklist, OrdenTrabajo
import logging

logger = logging.getLogger('gestion')

@login_required(login_url='web_login')
def dashboard(request):
    """
    Panel de Control Principal
    Muestra estadísticas generales de la flota y Alertas Críticas de Mantenimiento.
    Redirige a los roles operativos a sus respectivos módulos para evitar fuga visual de datos.
    """
    rol = request.user.rol
    if rol == 'OPERATOR':
        return redirect('checklist_list')
    elif rol == 'DISPATCHER':
        return redirect('orden_list')
    elif rol in ['FUEL', 'MECHANIC']:
        # Solo redirigir si TIENEN el módulo contratado, de otra forma déjalos en el dashboard
        if getattr(request.empresa, 'modulo_combustible', False):
            return redirect('combustible_dashboard')
        # Si no lo tiene, se renderiza el dashboard vacío o con mensajes de error
    # Filtro automático por empresa (EmpresaManager)
    total_maquinas = Maquinaria.objects.count()
    maquinas_en_ruta = Maquinaria.objects.filter(estado='EN_RUTA').count()
    maquinas_en_taller = Maquinaria.objects.filter(estado='TALLER').count()
    
    # Órdenes de Trabajo Activas (que todavía no tienen fecha de entrada)
    ordenes_activas = OrdenTrabajo.objects.filter(fecha_entrada__isnull=True).count()
    
    # Alertas Críticas (El Cerebro) -> Faltan <= 50 horas/km para mantenimiento
    # La DB evalúa: proximo_mantenimiento - valor_actual_medida <= 50 -> proximo_mantenimiento <= valor_actual_medida + 50
    alertas_mantenimiento = Maquinaria.objects.filter(
        proximo_mantenimiento__lte=F('valor_actual_medida') + 50
    ).exclude(estado='TALLER').order_by('proximo_mantenimiento')
    
    # --- Integración: Alertas desde Checklists de Terreno ---
    hace_48_horas = timezone.now() - timedelta(hours=48)
    checklists_recientes = Checklist.objects.filter(
        fecha_revision__gte=hace_48_horas
    ).exclude(
        maquina__estado='TALLER'
    ).exclude(
        # Excluir Checklists cuya falla ya fue gestionada en Taller
        # (existió una O.T. de Taller posterior a la fecha del Checklist)
        maquina__ordenes_taller__fecha_ingreso__gte=F('fecha_revision')
    ).order_by('-fecha_revision')
    
    # 1. Fallas Críticas (Niveles, Luces o Estructura están MAL)
    checklists_criticos = checklists_recientes.filter(
        Q(niveles_ok=False) | Q(luces_ok=False) | Q(estructura_ok=False)
    )
    
    # 2. Preventivas / No Críticas (Todo está OK, pero dejaron Comentarios)
    checklists_preventivos = checklists_recientes.filter(
        niveles_ok=True, luces_ok=True, estructura_ok=True
    ).exclude(comentarios__exact='').exclude(comentarios__isnull=True)
    
    # --- Integración: Alertas Operativas de Horario (Anti-Robo / Fuera de turno) ---
    ahora_local = timezone.localtime(timezone.now())
    hora_actual = ahora_local.hour
    
    # Obtenemos TODAS las OTs en curso (Las que salieron pero NO han regresado)
    ots_en_curso = OrdenTrabajo.objects.filter(empresa=request.empresa, fecha_entrada__isnull=True)
    
    # Madrugadores: Máquinas que salieron ANTES de las 08:00 AM de hoy o días anteriores
    alertas_madrugadores = []
    # Rezagados: Máquinas que siguen afuera y ya son más de las 19:00 PM (Hora Servidor)
    alertas_rezagados = []
    
    for ot in ots_en_curso:
        salida_local = timezone.localtime(ot.fecha_salida)
        if salida_local.hour < 8:
            alertas_madrugadores.append(ot)
        if hora_actual >= 19:
            alertas_rezagados.append(ot)
            
    logger.info(f"AUDITORÍA - Dashboard Consultado por Usuario: '{request.user.username}' de la empresa '{request.user.empresa.nombre_fantasia if request.user.empresa else 'System Admin'}'")
    
    context = {
        'total_maquinas': total_maquinas,
        'maquinas_en_ruta': maquinas_en_ruta,
        'maquinas_en_taller': maquinas_en_taller,
        'ordenes_activas': ordenes_activas,
        'alertas_mantenimiento': alertas_mantenimiento,
        'checklists_criticos': checklists_criticos,
        'checklists_preventivos': checklists_preventivos,
        'alertas_madrugadores': alertas_madrugadores,
        'alertas_rezagados': alertas_rezagados,
        'hora_actual_servidor': hora_actual,
    }
    return render(request, 'gestion/dashboard/index.html', context)
