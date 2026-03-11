from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, F
from ..models import OrdenTaller, Checklist, Maquinaria
from ..forms import OrdenTallerForm, OrdenTallerCloseForm
from ..utils import modulo_requerido
import json
import logging

logger = logging.getLogger(__name__)

@login_required(login_url='web_login')
@modulo_requerido('modulo_mantencion')
def taller_dashboard(request):
    ordenes_activas = OrdenTaller.objects.filter(empresa=request.empresa, estado__in=['EN_PROCESO', 'ESPERANDO_REPUESTO']).order_by('-fecha_ingreso')
    ordenes_historial = OrdenTaller.objects.filter(empresa=request.empresa, estado='FINALIZADO').order_by('-fecha_salida')[:50]
    
    # Checklists Fallidos (Últimas 48 horas)
    # Excluimos:
    # 1. Las máquinas ACTUALMENTE en Taller (ya están siendo atendidas)
    # 2. Los Checklists cuya máquina ya tiene una O.T. de Taller creada
    #    DESPUÉS del reporte del Checklist (es decir, ya fue gestionada y 
    #    posiblemente resuelta, no volver a mostrarla aunque la OT esté cerrada)
    hace_48_horas = timezone.now() - timezone.timedelta(hours=48)
    checklists_criticos = Checklist.objects.filter(
        empresa=request.empresa,
        fecha_revision__gte=hace_48_horas
    ).exclude(
        maquina__estado='TALLER'
    ).exclude(
        # Si la máquina tiene una OrdenTaller cuya fecha de ingreso es posterior
        # al momento en que se hizo el Checklist, significa que la falla ya fue
        # procesada en Taller (sin importar si la OT sigue abierta o ya cerró).
        maquina__ordenes_taller__fecha_ingreso__gte=F('fecha_revision')
    ).filter(
        Q(niveles_ok=False) | Q(luces_ok=False) | Q(estructura_ok=False)
    ).order_by('-fecha_revision')
    
    # Alertas Críticas de Mantenimiento (Por Horas/Km)
    alertas_mantenimiento = Maquinaria.objects.filter(
        empresa=request.empresa,
        proximo_mantenimiento__lte=F('valor_actual_medida') + 50
    ).exclude(estado='TALLER').order_by('proximo_mantenimiento')
    
    return render(request, 'gestion/taller/dashboard.html', {
        'ordenes_activas': ordenes_activas,
        'ordenes_historial': ordenes_historial,
        'checklists_criticos': checklists_criticos,
        'alertas_mantenimiento': alertas_mantenimiento
    })

@login_required(login_url='web_login')
def taller_create_ot(request):
    if request.method == 'POST':
        form = OrdenTallerForm(request.POST, empresa=request.empresa)
        if form.is_valid():
            nueva_ot = form.save(commit=False)
            nueva_ot.empresa = request.empresa
            # Si es mecánico o chief lo guardamos como asignado, si no, null
            if request.user.rol in ['MECHANIC', 'CHIEF', 'OWNER']:
                nueva_ot.mecanico = request.user
            nueva_ot.save()
            
            # Cambiar estado de la máquina a TALLER
            maquina = nueva_ot.maquina
            maquina.estado = 'TALLER'
            maquina.save(update_fields=['estado'])
            
            logger.info('OT TALLER ID=%s ABIERTA. Maquina=%s. Tipo=%s. Mecanico=%s. Empresa=%s.',
                        nueva_ot.pk, nueva_ot.maquina_id, nueva_ot.tipo_mantenimiento,
                        request.user.username, request.empresa.id)
            messages.success(request, 'Máquina ingresada a Taller exitosamente. Bloqueada para operaciones en Terreno.')
            return redirect('taller_dashboard')
        else:
            messages.error(request, 'Revise los errores en el formulario.')
    else:
        # 1. Verificar si nos enviaron una máquina específica por la URL (Ej: desde el panel Preventivo)
        maquina_id_from_url = request.GET.get('maquina')
        initial_data = {}
        
        if maquina_id_from_url:
            try:
                maquina_obj = get_object_or_404(Maquinaria, pk=maquina_id_from_url, empresa=request.empresa)
                initial_data = {
                    'maquina': maquina_obj,
                    'tipo_mantenimiento': 'PREVENTIVO',
                    'medida_ingreso': maquina_obj.valor_actual_medida
                }
            except Exception:
                pass # Si el ID es inválido, simplemente ignoramos y mostramos form en blanco
                
        form = OrdenTallerForm(empresa=request.empresa, initial=initial_data)
        
    # Extraemos medidas y operadores de las maquinas disponibles para autocompletar en el formulario
    maquinas = form.fields['maquina'].queryset
    medidas_map   = {m.id: float(m.valor_actual_medida) if m.valor_actual_medida is not None else 0.0 for m in maquinas}
    operadores_map = {m.id: m.operador_asignado.id for m in maquinas if m.operador_asignado}

    return render(request, 'gestion/taller/ot_form.html', {
        'form': form,
        'titulo': 'Nuevo Ingreso a Taller',
        'btn_texto': 'Ingresar a Taller',
        'medidas_map': medidas_map,
        'operadores_map': operadores_map,
    })

@login_required(login_url='web_login')
def taller_close_ot(request, pk):
    orden = get_object_or_404(OrdenTaller, pk=pk, empresa=request.empresa, estado__in=['EN_PROCESO', 'ESPERANDO_REPUESTO'])
    
    if request.method == 'POST':
        form = OrdenTallerCloseForm(request.POST, instance=orden)
        if form.is_valid():
            orden_cerrada = form.save(commit=False)
            orden_cerrada.estado = 'FINALIZADO'
            orden_cerrada.fecha_salida = timezone.now()
            
            maquina = orden_cerrada.maquina
            
            # Actualizar la medida actual de la máquina si entregó un valor distinto
            if orden_cerrada.medida_salida and orden_cerrada.medida_salida >= orden_cerrada.medida_ingreso:
                 maquina.valor_actual_medida = orden_cerrada.medida_salida
            
            # Verificamos si pidió resetear el mantenimiento
            actualizar_mantenimiento = form.cleaned_data.get('update_mantenimiento', False)
            if actualizar_mantenimiento:
                # Buscar configuración de la empresa o usar defaults de seguridad
                try:
                    config = request.empresa.configuracion_mantencion
                    incremento = config.intervalo_horas if maquina.unidad_medida == 'HORAS' else config.intervalo_km
                except Exception:
                    # En caso de que la empresa antigua no haya guardado configuración aún (retrocompatibilidad)
                    incremento = 250 if maquina.unidad_medida == 'HORAS' else 10000
                
                # Sumamos el rango dinámico de la Empresa al valor actual
                maquina.proximo_mantenimiento = maquina.valor_actual_medida + incremento
                
            # Liberamos la máquina
            maquina.estado = 'DISPONIBLE'
            maquina.save(update_fields=['estado', 'valor_actual_medida', 'proximo_mantenimiento'])
            
            orden_cerrada.save()
            logger.info('OT TALLER ID=%s CERRADA. Maquina=%s. Mantenimiento_reset=%s. Mecanico=%s. Empresa=%s.',
                        orden_cerrada.pk, maquina.id, actualizar_mantenimiento,
                        request.user.username, request.empresa.id)
            messages.success(request, 'Orden de Taller finalizada. Máquina liberada, mantenimiento recalculado y lista para operar.')
            return redirect('taller_dashboard')
    else:
        # Pre-llenamos el horómetro de salida con el de ingreso
        form = OrdenTallerCloseForm(instance=orden, initial={'medida_salida': orden.medida_ingreso})
        
    return render(request, 'gestion/taller/ot_close.html', {
        'form': form,
        'orden': orden
    })

@login_required(login_url='web_login')
def taller_update_estado(request, pk):
    # Endpoint rápido para cambiar estado a Esperando Repuesto sin cerrar la OT
    if request.method == 'POST':
        orden = get_object_or_404(OrdenTaller, pk=pk, empresa=request.empresa)
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(OrdenTaller.ESTADOS_TALLER).keys() and nuevo_estado != 'FINALIZADO':
            orden.estado = nuevo_estado
            orden.save(update_fields=['estado'])
            logger.info('OT TALLER ID=%s cambio estado a %s. Usuario=%s. Empresa=%s.',
                        pk, nuevo_estado, request.user.username, request.empresa.id)
            messages.success(request, f'Estado de Equipo actualizado a: {orden.get_estado_display()}')
    return redirect('taller_dashboard')

@login_required(login_url='web_login')
def taller_create_from_checklist(request, checklist_id):
    """
    Atajo inteligente para crear una Orden de Taller auto-llenada
    en base a un reporte de terreno fallido.
    """
    checklist = get_object_or_404(Checklist, pk=checklist_id, empresa=request.empresa)
    
    # Evitar crear dobles si la máquina ya se ingresó al taller
    if checklist.maquina.estado == 'TALLER':
        messages.warning(request, f'La máquina {checklist.maquina.id_interno} ya se encuentra en el Taller.')
        return redirect('taller_dashboard')
        
    # Inicializar el formulario con los datos pre-rellenados
    falla_desc = f"[AUTO-REPORTE] Checklist reportado por {checklist.usuario.get_full_name() or checklist.usuario.username}:\n"
    if not checklist.niveles_ok: falla_desc += "- Falla de Niveles de fluidos\n"
    if not checklist.luces_ok: falla_desc += "- Falla de Luces u Óptica\n"
    if not checklist.estructura_ok: falla_desc += "- Falla de Estructura / Carrocería\n"
    if checklist.comentarios: falla_desc += f"\nNotas: {checklist.comentarios}"
    
    initial_data = {
        'maquina': checklist.maquina,
        'tipo_mantenimiento': 'CORRECTIVO', # Si viene de un fallo es correctivo
        'descripcion_falla': falla_desc,
        'medida_ingreso': checklist.maquina.valor_actual_medida,
    }
    
    form = OrdenTallerForm(initial=initial_data, empresa=request.empresa)
    
    # Extraemos el json de medidas por si el operario cambia la select box a última hora
    maquinas = form.fields['maquina'].queryset
    medidas_map = {m.id: float(m.valor_actual_medida) for m in maquinas if m.valor_actual_medida is not None}
    
    return render(request, 'gestion/taller/ot_form.html', {
        'form': form,
        'titulo': f'Abrir OT para Máquina {checklist.maquina.id_interno}',
        'btn_texto': 'Confirmar y Bloquear Máquina',
        'medidas_map': json.dumps(medidas_map)
    })
