
# Roles, Seguridad y Operacion

## 1. Roles del sistema

### 1.1 STORE_USER
Usuario operativo de tienda.

#### Permisos funcionales
- consultar tickets visibles para sus tiendas;
- visualizar cabecera, detalle y distribucion;
- cargar archivo escaneado si `source_status_code = '9'`;
- reemplazar archivo si no esta confirmado;
- confirmar archivo;
- visualizar archivo activo.

#### Restricciones
- no ver tickets de tiendas no asignadas;
- no modificar datos base del ticket;
- no administrar usuarios;
- no administrar lotes ni configuracion tecnica.

### 1.2 SUPERVISOR
Usuario con vision global operativa.

#### Permisos funcionales
- ver cualquier ticket;
- consultar cabecera, detalle, distribucion y archivo;
- filtrar por tienda, lote, fecha, estatus;
- monitorear tickets con/sin archivo;
- apoyar seguimiento operativo.

### 1.3 ADMIN
Usuario administrador del sistema.

#### Permisos funcionales
- todo lo de supervisor;
- administrar usuarios;
- administrar roles;
- asignar tiendas a usuarios;
- consultar lotes, errores y auditoria;
- gestionar parametros si a futuro se habilitan.

## 2. Seguridad por tienda
La autorizacion de tickets para `STORE_USER` se construye con esta relacion:

```text
ticket
  -> ticket_store
  -> app_user_store
```

### Regla exacta
Un `STORE_USER` puede ver un ticket si existe al menos una `store_code` del ticket que este asignada al usuario en `app_user_store`.

## 3. Estrategia de seguridad recomendada

### 3.1 En backend
El backend debe:
- autenticar al usuario;
- resolver su rol;
- resolver sus tiendas (si aplica);
- filtrar consultas segun rol;
- bloquear operaciones no permitidas.

### 3.2 En base de datos
La base de datos debe:
- mantener integridad de relaciones;
- proteger reglas del archivo escaneado;
- auditar eventos;
- idealmente restringir DML directo sobre tablas sensibles.

## 4. Casos de autorizacion

### Caso A: STORE_USER consulta ticket
Permitir solo si existe match de tienda.

### Caso B: STORE_USER sube/reemplaza archivo
Permitir solo si:
- tiene acceso al ticket por tienda,
- el ticket tiene `source_status_code = '9'`,
- no hay archivo confirmado activo.

### Caso C: STORE_USER confirma archivo
Permitir solo si:
- tiene acceso al ticket por tienda,
- existe archivo activo,
- el archivo no esta confirmado.

### Caso D: SUPERVISOR
Permitir operaciones de consulta global sin filtro de tienda.

### Caso E: ADMIN
Permitir administracion de seguridad y operacion completa.

## 5. Seguridad recomendada de la interfaz web

### Pantallas para STORE_USER
- Login
- Consulta de tickets de sus tiendas
- Detalle del ticket
- Carga/reemplazo/confirmacion del archivo escaneado
- Visualizacion del archivo

### Pantallas para SUPERVISOR
- Dashboard operativo
- Consulta global de tickets
- Detalle y visualizacion
- Monitoreo de tickets con/sin archivo

### Pantallas para ADMIN
- Todo lo anterior
- Usuarios
- Roles
- Asignacion de tiendas
- Lotes
- Errores de integracion
- Auditoria

## 6. Seguridad recomendada a nivel BD

### Recomendacion critica
El usuario tecnico del backend **no debe** tener libertad total sobre tablas delicadas.

#### Recomendado
- lectura controlada en tablas operativas;
- ejecucion de funciones/procedimientos para archivo escaneado;
- acceso controlado a tablas de seguridad;
- no permitir `DELETE` directo sobre ticket/ticket_scan_file.

## 7. Eventos a auditar
Se debe auditar como minimo:
- inicio/fin de lotes;
- errores de integracion;
- carga inicial de archivo;
- reemplazo de archivo;
- confirmacion de archivo;
- administracion de usuarios;
- cambios de rol;
- cambios de tiendas asignadas.

## 8. Codigos de evento sugeridos para `audit_event`
- `BATCH_CREATED`
- `BATCH_PROCESSED`
- `BATCH_FAILED`
- `TICKET_CREATED`
- `SCAN_FILE_UPLOADED`
- `SCAN_FILE_REPLACED`
- `SCAN_FILE_CONFIRMED`
- `USER_CREATED`
- `USER_UPDATED`
- `ROLE_ASSIGNED`
- `STORE_ASSIGNED`

## 9. Principios de operacion diaria
- los lotes se revisan primero;
- los tickets nuevos se consolidan;
- las tiendas consultan sus tickets;
- las tiendas adjuntan/confirmar escaneo cuando corresponda;
- supervisores monitorean cobertura documental;
- administradores atienden errores, seguridad y soporte.
