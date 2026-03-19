# 🚜 MaqLogik - Gestión SaaS Móvil de Maquinaria Pesada

MaqLogik es una plataforma SaaS (Software as a Service) diseñada para la gestión integral de flotas de maquinaria pesada. Centraliza el control de costos operativo, mantenimiento preventivo y telemetría utilizando smartphones como hardware de campo.

## 🛠️ Stack Tecnológico
- **Backend:** Python 3.11 + Django 4.2
- **Base de Datos:** MySQL 8.0
- **Asincronía:** Celery + Redis
- **Infraestructura:** Docker & Docker-Compose
- **Frontend Web:** Django Templates + HTMX + Vanilla CSS (Glassmorphism)
- **Seguridad:** Cloudflare Tunnels (Producción)

## 🚀 Inicio Rápido (Desarrollo)

### 1. Clonar e Instalar
```bash
git clone [url-del-repositorio]
cd MaqLogik
```

### 2. Configurar Entorno
Crea un archivo `.env` en la raíz basado en el ejemplo configurado para Docker.

### 3. Levantar con Docker
```bash
docker-compose up -d --build
```
*Nota: La base de datos MySQL estará disponible en el puerto host `3307`.*

### 4. Inicializar Aplicación
```bash
docker exec -it maqlogik_web python manage.py migrate
docker exec -it maqlogik_web python manage.py createsuperuser
```

## 📂 Estructura del Proyecto
- `/src`: Código fuente de Django.
    - `/gestion`: App principal (Modelos de negocio, Vistas Web y API).
    - `/config`: Configuración global del proyecto.
- `docker-compose.yml`: Definición de microservicios.
- `ARCHITECTURE.md`: Detalle técnico de la arquitectura multi-tenant.

## 👥 Roles y Flujo
- **Owner/Chief:** Gestión de flota, usuarios y reportes financieros.
- **Operador:** Checklists diarios desde App, cargas de combustible y GPS.
- **Mecánico:** Gestión de órdenes de taller y reparaciones.

---
**Desarrollado por:** Antigravity AI Architect.
