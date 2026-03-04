from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Checklist
from ..forms import ChecklistForm

@login_required
def checklist_list(request):
    # Base: Todas las revisiones de esta Empresa (Multi-tenancy)
    qs = Checklist.objects.filter(empresa=request.empresa)
    
    # RBAC: Si el usuario es OPERADOR, solo puede ver las revisiones que él mismo ha enviado
    if request.user.rol == 'OPERATOR':
        qs = qs.filter(usuario=request.user)
        
    checklists = qs.order_by('-fecha_revision')
    
    return render(request, 'gestion/checklists/checklist_list.html', {'checklists': checklists})

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
                messages.warning(request, 'Revisión registrada con observaciones. La máquina requiere atención.')
            else:
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
