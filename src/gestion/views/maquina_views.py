from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from ..models import Maquinaria
from ..forms import MaquinariaForm
import logging

logger = logging.getLogger('gestion')

@login_required(login_url='web_login')
def maquina_list(request):
    # Parámetros de ordenamiento web y Búsqueda global
    search_query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'id_interno')
    direction = request.GET.get('dir', 'asc')
    
    # Prevenir inyección o errores de campos inexistentes limitando los permitidos
    campos_permitidos = ['id_interno', 'patente', 'tipo', 'marca', 'operador_asignado__username', 'estado', 'valor_actual_medida']
    if sort_by not in campos_permitidos:
        sort_by = 'id_interno'
        
    order_string = f"-{sort_by}" if direction == 'desc' else sort_by

    # Se listan solo las máquinas de la Empresa (Filtro base asumido o global)
    maquinarias = Maquinaria.objects.all()

    # Si hay búsqueda global
    if search_query:
        maquinarias = maquinarias.filter(
            Q(id_interno__icontains=search_query) |
            Q(patente__icontains=search_query) |
            Q(marca__icontains=search_query) |
            Q(modelo__icontains=search_query)
        )

    maquinarias = maquinarias.order_by(order_string)
    
    # --- Paginación ---
    paginator = Paginator(maquinarias, 20) # 20 ítems por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    logger.info(f"AUDITORÍA - Acceso a Listado de Maquinarias. Búsqueda: '{search_query}'. Por: '{request.user.username}'")
    return render(request, 'gestion/maquinarias/lista.html', {
        'maquinarias': page_obj, # Cambiamos maquinarias completas por el objeto página
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': paginator.num_pages > 1,
        'current_sort': sort_by,
        'current_dir': direction
    })

@login_required(login_url='web_login')
def maquina_create(request):
    # Guardia SaaS: El usuario DEBE pertenecer a una empresa
    if not request.user.empresa:
        messages.error(request, 'Atención SuperAdmin: Debes asignarte a una Empresa desde el panel de /admin antes de registrar maquinaria.')
        return redirect('maquina_list')

    if request.method == 'POST':
        form = MaquinariaForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            maquina = form.save(commit=False)
            # Inyección silenciosa del Tenant (Empresa) del usuario logueado
            maquina.empresa = request.user.empresa
            maquina.save()
            messages.success(request, 'La máquina ha sido registrada con éxito.')
            logger.info(f"AUDITORÍA - Nueva Maquinaria '{maquina.id_interno}' registrada por: '{request.user.username}'")
            return redirect('maquina_list')
        else:
            messages.error(request, 'Hubo un error en el formulario, revisa los datos ingresados.')
    else:
        form = MaquinariaForm(empresa=request.user.empresa)
    
    return render(request, 'gestion/maquinarias/formulario.html', {'form': form, 'accion': 'Registrar'})

@login_required(login_url='web_login')
def maquina_update(request, pk):
    # El usuario solo podrá encontrar máquinas de su empresa
    maquina = get_object_or_404(Maquinaria, pk=pk)
    
    if request.method == 'POST':
        form = MaquinariaForm(request.POST, instance=maquina, empresa=request.user.empresa)
        if form.is_valid():
            form.save()
            messages.success(request, 'La máquina se ha actualizado correctamente.')
            logger.info(f"AUDITORÍA - Maquinaria '{maquina.id_interno}' editada por: '{request.user.username}'")
            return redirect('maquina_list')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = MaquinariaForm(instance=maquina, empresa=request.user.empresa)
        
    return render(request, 'gestion/maquinarias/formulario.html', {'form': form, 'accion': 'Editar', 'maquina': maquina})
