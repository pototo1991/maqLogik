from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import Checklist
from ..forms import ChecklistForm
import logging

logger = logging.getLogger(__name__)

@login_required
def checklist_list(request):
    # Base: Todas las revisiones de esta Empresa (Multi-tenancy)
    qs = Checklist.objects.filter(empresa=request.empresa)
    
    # RBAC: Si el usuario es OPERADOR, solo puede ver las revisiones que él mismo ha enviado
    if request.user.rol == 'OPERATOR':
        qs = qs.filter(usuario=request.user)
        
    checklists = qs.order_by('-fecha_revision')
    
    # --- Paginación ---
    paginator = Paginator(checklists, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'gestion/checklists/checklist_list.html', {
        'checklists': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': paginator.num_pages > 1,
    })

@login_required
def checklist_create(request):
    if request.method == 'POST':
        # Pasamos el kwargs 'empresa' que definimos en el ModelForm __init__
        form = ChecklistForm(request.POST, empresa=request.empresa)
        if form.is_valid():
            nuevo_checklist = form.save(commit=False)
            nuevo_checklist.empresa = request.empresa
            nuevo_checklist.usuario = request.user
            nuevo_checklist.save()
            
            # Notificar dependiendo del estado de la máquina
            if not nuevo_checklist.niveles_ok or not nuevo_checklist.luces_ok or not nuevo_checklist.estructura_ok:
                logger.warning('Checklist ID=%s con observaciones. Maquina=%s. Usuario=%s. Empresa=%s.',
                               nuevo_checklist.pk, nuevo_checklist.maquina_id, request.user.username, request.empresa.id)
                messages.warning(request, 'Revisión registrada con observaciones. La máquina requiere atención.')
            else:
                logger.info('Checklist ID=%s registrado OK. Maquina=%s. Usuario=%s. Empresa=%s.',
                            nuevo_checklist.pk, nuevo_checklist.maquina_id, request.user.username, request.empresa.id)
                messages.success(request, 'Checklist registrado correctamente. Equipo operativo.')
                
            return redirect('checklist_list')
        else:
            messages.error(request, 'Error al registrar la revisión.')
    else:
        form = ChecklistForm(empresa=request.empresa)
    
    import json
    # Mapeo de operador fijo por máquina para autocompletar en frontend
    maquinas = form.fields['maquina'].queryset
    operadores_map = {m.id: m.operador_asignado.id for m in maquinas if m.operador_asignado}
        
    return render(request, 'gestion/checklists/checklist_form.html', {
        'form': form,
        'titulo': 'Nueva Revisión Diaria',
        'operadores_map': json.dumps(operadores_map)
    })
