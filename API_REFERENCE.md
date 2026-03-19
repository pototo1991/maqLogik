# 📡 Referencia de API MaqLogik (Mobile)

Esta API permite la integración de aplicaciones móviles para el registro de datos en terreno.

## 1. Autenticación (JWT)

### Obtener Token (Login)
- **Endpoint:** `POST /api/v1/auth/login/`
- **Payload:**
  ```json
  {"username": "usuario", "password": "password"}
  ```
- **Respuesta:**
  ```json
  {"refresh": "...", "access": "..."}
  ```

### Refrescar Token
- **Endpoint:** `POST /api/v1/auth/refresh/`
- **Payload:** `{"refresh": "..."}`

## 2. Endpoints de Negocio
Todos los endpoints requieren el header `Authorization: Bearer <access_token>`.

### Maquinaria
- `GET /api/v1/maquinarias/`: Lista de máquinas de la empresa.
- `GET /api/v1/mis-maquinas/`: Máquinas asignadas al operador logueado.

### Operatividad
- `POST /api/v1/checklists/`: Registro de nueva inspección diaria.
- `POST /api/v1/ordenes/`: Apertura/Cierre de Orden de Trabajo.
- `POST /api/v1/gps/`: Envío de coordenadas GPS (Logs).
- `POST /api/v1/combustible/`: Registro de carga de combustible.

## 3. Consideraciones Técnicas
- **Aislamiento:** La API filtra automáticamente por la empresa asociada al usuario del token.
- **Formato:** Todas las respuestas son en **JSON**.
- **Errores:** Los errores de validación (`400 Bad Request`) incluyen detalles por campo.
