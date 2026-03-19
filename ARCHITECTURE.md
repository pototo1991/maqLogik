# 🏗️ Arquitectura Técnica de MaqLogik

Este documento detalla los pilares del diseño de MaqLogik, diseñado para ser un SaaS multi-tenant escalable y seguro.

## 1. Aislamiento Multi-tenant (SaaS)
La privacidad de los datos es el corazón del sistema. Cada cliente (Empresa) está estrictamente aislado de los demás.

### EmpresaMiddleware
Ubicado en `src/gestion/middleware.py`, este middleware captura la empresa del usuario autenticado (o la sesión de impersonación para superadmins) y la almacena en un objeto `thread-local`.

### EmpresaManager
Los modelos de negocio utilizan un manager personalizado (`EmpresaManager`) que filtra automáticamente todos los QuerySets:
```python
def get_queryset(self):
    empresa_actual = get_current_empresa()
    return super().get_queryset().filter(empresa=empresa_actual)
```

## 2. Modelos de Datos (Las 10 Tablas)
El sistema gestiona 10 entidades principales para cubrir el ciclo de vida de la maquinaria:

1.  **Empresas:** Raíz del tenant. Controla qué módulos están activos (`modulo_checklist`, `modulo_gps`, etc.).
2.  **Usuarios:** Basado en `AbstractUser`, con roles predefinidos (`OWNER`, `CHIEF`, `OPERATOR`, `MECHANIC`, etc.).
3.  **Maquinaria:** Inventario de activos con horómetro/km actual y consumo teórico.
4.  **Checklist:** Inspecciones preventivas diarias.
5.  **OrdenTrabajo:** Registro de actividad operativa (Salida/Entrada).
6.  **GPSLog:** Telemetría enviada desde dispositivos móviles.
7.  **CombustibleLog:** Registro de cargas internas y externas.
8.  **CompraCombustible:** Abastecimiento del tanque de patio.
9.  **InventarioCombustible:** Stock actual y Precio Promedio Ponderado por empresa.
10. **OrdenTaller:** Gestión de mantenimiento preventivo y correctivo.

## 3. Reglas de Negocio Críticas
- **Validación de Seguridad:** No se puede abrir una Orden de Trabajo si no existe un Checklist aprobado en las últimas 12 horas para esa máquina específica.
- **Cálculo de Rendimiento:** El sistema cruza datos de `OrdenTrabajo` y `CombustibleLog` para alertar sobre desviaciones anormales en el consumo de litros/hora.
- **Control de Inventario:** Las cargas internas de combustible disparan una alerta de stock crítico basada en la configuración de la empresa.

## 4. Seguridad en Producción
En el entorno `Knossos`, el sistema utiliza:
- **Cloudflare Tunnels:** Para exponer la aplicación sin abrir puertos públicos.
- **CSRF Trusted Origins:** Configurado para confiar únicamente en `maqlogik.cl` y subdominios.
- **SECURE_PROXY_SSL_HEADER:** Permite a Django detectar correctamente conexiones HTTPS detrás del túnel.
