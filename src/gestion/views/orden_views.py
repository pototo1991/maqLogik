from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..models import OrdenTrabajo
from ..forms import OrdenTrabajoSalidaForm, OrdenTrabajoEntradaForm

@login_required
def orden_list(request):
    # Parametros de ordenamiento
    sort_by = request.GET.get('sort', 'fecha_salida')
    direction = request.GET.get('dir', 'desc') # Por defecto desc para OTs (las mas nuevas primero)
    
    campos_permitidos = ['fecha_salida', 'maquina__id_interno', 'operador__username', 'nro_guia_despacho', 'medida_salida']
    if sort_by not in campos_permitidos:
        sort_by = 'fecha_salida'
        
    order_string = f"-{sort_by}" if direction == 'desc' else sort_by

    ordenes = OrdenTrabajo.objects.filter(empresa=request.empresa).order_by(order_string)
    
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
    
    return render(request, 'gestion/ordenes/orden_list.html', {
        'ordenes': ordenes,
        'current_sort': sort_by,
        'current_dir': direction,
        'alertas_madrugadores': alertas_madrugadores,
        'alertas_rezagados': alertas_rezagados,
        'hora_actual_servidor': hora_actual,
    })

@login_required
def orden_create(request):
    if request.method == 'POST':
        form = OrdenTrabajoSalidaForm(request.POST, empresa=request.empresa)
        if form.is_valid():
            nueva_orden = form.save(commit=False)
            nueva_orden.empresa = request.empresa
            # Si el logueado es despachador, lo registramos así. Si es el operador directo, no hay despachador.
            if request.user.rol == 'DISPATCHER':
                 nueva_orden.despachador = request.user
                 
            try:
                # Al llamar save(), el modelo ejecuta clean(), que valida el Checklist de las ultimas 12 horas.
                nueva_orden.save()
                
                # Actualizar estado de la maquina a EN_RUTA
                maquina = nueva_orden.maquina
                maquina.estado = 'EN_RUTA'
                maquina.save(update_fields=['estado'])
                
                messages.success(request, 'Orden de Trabajo (Salida) generada correctamente.')
                return redirect('orden_list')
            except ValidationError as e:
                # Mostrar el error específico proveniente del model validation (Ej. Falta checklist o fallas criticas)
                messages.error(request, e.message if hasattr(e, 'message') else str(e))
        else:
            messages.error(request, 'Por favor, revise los datos del formulario.')
    else:
        form = OrdenTrabajoSalidaForm(empresa=request.empresa)
        
    import json
    maquinas = form.fields['maquina'].queryset
    operadores_map = {m.id: m.operador_asignado.id for m in maquinas if m.operador_asignado}
    medidas_map = {m.id: float(m.valor_actual_medida) for m in maquinas if m.valor_actual_medida is not None}
        
    return render(request, 'gestion/ordenes/orden_form.html', {
        'form': form,
        'titulo': 'Nueva Orden de Trabajo (Salida)',
        'btn_texto': 'Registrar Salida',
        'operadores_map': json.dumps(operadores_map),
        'medidas_map': json.dumps(medidas_map)
    })

@login_required
def orden_close(request, pk):
    orden = get_object_or_404(OrdenTrabajo, pk=pk, empresa=request.empresa, fecha_entrada__isnull=True)
    
    if request.method == 'POST':
        form = OrdenTrabajoEntradaForm(request.POST, instance=orden)
        if form.is_valid():
            orden_cerrada = form.save(commit=False)
            orden_cerrada.fecha_entrada = timezone.now()
            
            # Validación simple: la entrada debe ser mayor o igual a la salida
            if orden_cerrada.medida_entrada < orden_cerrada.medida_salida:
                messages.error(request, 'El Horómetro/Km de entrada no puede ser menor al de salida.')
            else:
                orden_cerrada.save()
                
                # Regla de Negocio: Actualizar el odómetro de la Máquina y dejarla DISPONIBLE de nuevo
                maquina = orden_cerrada.maquina
                maquina.valor_actual_medida = orden_cerrada.medida_entrada
                maquina.estado = 'DISPONIBLE'
                maquina.save(update_fields=['valor_actual_medida', 'estado'])
                
                messages.success(request, 'Orden de Trabajo cerrada exitosamente. Máquina disponible.')
                return redirect('orden_list')
    else:
        # Pre-llenar con la medida sugerida por reglas de negocio
        medida_sugerida = orden.medida_salida
        if orden.maquina.unidad_medida == 'HORAS':
            tiempo_transcurrido = timezone.now() - orden.fecha_salida
            horas_transcurridas = tiempo_transcurrido.total_seconds() / 3600.0
            
            # Cobro mínimo de 2 horas o tiempo real si fue mayor
            horas_a_sumar = max(2.0, horas_transcurridas)
            medida_sugerida = float(orden.medida_salida) + horas_a_sumar
            
            # Redondeamos a 1 decimal para la vista
            medida_sugerida = round(medida_sugerida, 1)

        form = OrdenTrabajoEntradaForm(instance=orden, initial={'medida_entrada': medida_sugerida})
        
    return render(request, 'gestion/ordenes/orden_form.html', {
        'form': form,
        'titulo': f'Cerrar OT: {orden.maquina.id_interno}',
        'btn_texto': 'Registrar Llegada',
        'is_cierre': True,
        'orden': orden
    })
