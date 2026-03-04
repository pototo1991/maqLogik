from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Usuario
from ..forms import UsuarioCreationForm, UsuarioUpdateForm

@login_required
def usuario_list(request):
    # Parametros de ordenamiento
    sort_by = request.GET.get('sort', 'username')
    direction = request.GET.get('dir', 'asc')
    
    campos_permitidos = ['username', 'nombre_completo', 'rol', 'estado', 'rut', 'valor_hora']
    if sort_by not in campos_permitidos:
        sort_by = 'username'
        
    order_string = f"-{sort_by}" if direction == 'desc' else sort_by

    usuarios = Usuario.objects.filter(empresa=request.empresa).exclude(is_superuser=True).order_by(order_string)
    
    return render(request, 'gestion/usuarios/usuario_list.html', {
        'usuarios': usuarios,
        'current_sort': sort_by,
        'current_dir': direction
    })

@login_required
def usuario_create(request):
    # Idealmente, solo dueños (OWNER) o administradores (CHIEF) deberían crear usuarios
    # Si quisieras validarlo: if request.user.rol not in ['OWNER', 'CHIEF']: return redirect('dashboard')
    
    if request.method == 'POST':
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            nuevo_usuario = form.save(commit=False)
            nuevo_usuario.empresa = request.empresa # Asignación crtítica SaaS
            nuevo_usuario.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('usuario_list')
        else:
            messages.error(request, 'Error al crear el usuario. Revisa los datos.')
    else:
        form = UsuarioCreationForm()
        
    return render(request, 'gestion/usuarios/usuario_form.html', {
        'form': form,
        'titulo': 'Nuevo Usuario',
        'btn_texto': 'Crear Usuario'
    })

@login_required
def usuario_update(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk, empresa=request.empresa) # Seguridad SaaS
    
    if request.method == 'POST':
        form = UsuarioUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('usuario_list')
        else:
            messages.error(request, 'Error al actualizar el usuario.')
    else:
        form = UsuarioUpdateForm(instance=usuario)
        
    return render(request, 'gestion/usuarios/usuario_form.html', {
        'form': form,
        'titulo': f'Editar Usuario: {usuario.username}',
        'btn_texto': 'Guardar Cambios'
    })
