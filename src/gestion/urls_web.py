from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views.landing_views import landing_page

urlpatterns = [
    path('', landing_page, name='home'),  # Landing Page Pública
    path('login/', views.web_login, name='web_login'),
    path('logout/', views.web_logout, name='web_logout'),
    path('perfil/', views.mi_perfil, name='mi_perfil'),
    path('cambiar-password/', views.cambiar_password_forzado, name='cambiar_password_forzado'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # --- Auth: Recuperación de Contraseña ---
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='gestion/auth/password_reset_form.html', email_template_name='gestion/auth/password_reset_email.html', success_url='/password_reset/done/'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='gestion/auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='gestion/auth/password_reset_confirm.html', success_url='/reset/done/'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='gestion/auth/password_reset_complete.html'), name='password_reset_complete'),
    
    # --- Maquinarias ---
    path('maquinarias/', views.maquina_list, name='maquina_list'),
    path('maquinarias/nueva/', views.maquina_create, name='maquina_create'),
    path('maquinarias/<int:pk>/editar/', views.maquina_update, name='maquina_update'),

    # --- Usuarios ---
    path('usuarios/', views.usuario_list, name='usuario_list'),
    path('usuarios/nuevo/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:pk>/editar/', views.usuario_update, name='usuario_update'),

    # --- Checklists ---
    path('checklists/', views.checklist_list, name='checklist_list'),
    path('checklists/nuevo/', views.checklist_create, name='checklist_create'),

    # --- Ordenes de Trabajo ---
    path('ordenes/', views.orden_list, name='orden_list'),
    path('ordenes/nueva/', views.orden_create, name='orden_create'),
    path('ordenes/<int:pk>/cerrar/', views.orden_close, name='orden_close'),

    # --- Combustible ---
    path('combustible/', views.combustible_dashboard, name='combustible_dashboard'),
    path('combustible/recargar/', views.carga_create, name='carga_create'),
    path('combustible/comprar/', views.compra_create, name='compra_create'),
    path('api/combustible/maquina/<int:maquina_id>/ot_abierta/', views.api_ot_abierta, name='api_ot_abierta'),

    # --- Tracking ---
    path('mapa/', views.mapa_en_vivo, name='mapa_live'),
    path('api/gps/posiciones/', views.api_posiciones, name='api_posiciones'),

    # --- Taller Mecánico ---
    path('taller/', views.taller_dashboard, name='taller_dashboard'),
    path('taller/nueva/', views.taller_create_ot, name='taller_create_ot'),
    path('taller/nueva/desde-checklist/<int:checklist_id>/', views.taller_create_from_checklist, name='taller_create_from_checklist'),
    path('taller/ot/<int:pk>/estado/', views.taller_update_estado, name='taller_update_estado'),
    path('taller/ot/<int:pk>/cerrar/', views.taller_close_ot, name='taller_close_ot'),

    # --- Reportería y Exportaciones PDF ---
    path('reportes/', views.reportes_dashboard, name='reportes_dashboard'),
    path('reportes/descargar/<str:tipo_reporte>/', views.generar_pdf, name='generar_pdf'),
    
    # --- Panel de Administración Maestro (Root SaaS) ---
    path('root/', views.root_dashboard, name='root_dashboard'),
    path('root/nueva/', views.root_create_empresa, name='root_create_empresa'),
    path('root/empresa/<int:empresa_id>/modulos/', views.root_edit_modules, name='root_edit_modules'),
    path('root/empresa/<int:empresa_id>/owner/', views.root_manage_owner, name='root_manage_owner'),
    path('root/empresa/<int:empresa_id>/toggle-status/', views.root_toggle_empresa_status, name='root_toggle_empresa_status'),
    path('root/empresa/<int:empresa_id>/importar-usuarios/', views.root_import_usuarios, name='root_import_usuarios'),
    path('root/empresa/<int:empresa_id>/bajar-plantilla/', views.root_download_plantilla_usuarios, name='root_download_plantilla_usuarios'),
    path('root/empresa/<int:empresa_id>/importar-maquinas/', views.root_import_maquinarias, name='root_import_maquinarias'),
    path('root/empresa/<int:empresa_id>/bajar-plantilla-maquinas/', views.root_download_plantilla_maquinarias, name='root_download_plantilla_maquinarias'),
    
    # --- Exportaciones CSV Genéricas ---
    path('exportar/csv/<str:tipo>/', views.exportar_csv, name='exportar_csv'),
    
    # --- Impersonation (Ver como Cliente) ---
    path('root/empresa/<int:empresa_id>/impersonate/', views.root_impersonate, name='root_impersonate'),
    path('root/impersonate/stop/', views.root_stop_impersonate, name='root_stop_impersonate'),
]
