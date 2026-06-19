
# Vision, Alcance y Reglas del Proyecto

## 1. Vision general
El sistema web de gestion de tickets de competencia se construira para sustituir el uso operativo/documental actual de InvesDoc en el proceso de consulta y control de tickets de competencia.

El nuevo sistema **no inicia capturando manualmente tickets**. En esta fase del proyecto, la fuente base del ticket ya existe y se genera desde el ecosistema SAP/AS400.

### Vision funcional
El nuevo sistema debe ser capaz de:
- recibir tickets ya integrados desde AS400,
- consolidarlos en una base de datos propia,
- permitir su consulta por usuarios autorizados,
- controlar acceso por tienda,
- asociar posteriormente un archivo escaneado del ticket,
- confirmar el archivo escaneado,
- bloquear su reemplazo despues de confirmarse,
- conservar trazabilidad tecnica y funcional.

## 2. Problema de negocio que resuelve
Actualmente el proceso depende de una solucion documental existente. El objetivo es construir una plataforma propia con mejor control funcional, tecnico y operativo.

### Necesidades del negocio
- centralizar el conocimiento del ticket en una base propia;
- eliminar dependencia funcional de la herramienta actual;
- separar claramente integracion, operacion y visualizacion;
- habilitar evolucion futura a reporteo e integracion con otros componentes;
- controlar seguridad por tienda y roles;
- manejar el ticket escaneado como consulta documental.

## 3. Fuente actual de informacion
La informacion del ticket ya existe en AS400 y se distribuye en estas tablas:

### 3.1 SAPRCTGH
Tabla origen de **cabecera de ticket**.
Responsabilidades funcionales:
- identifica el ticket,
- contiene su estatus de origen,
- determina si se puede adjuntar archivo (estatus 9),
- representa la entidad principal del ticket.

### 3.2 SAPRCTGD
Tabla origen de **detalle del ticket**.
Responsabilidades funcionales:
- contiene productos/conceptos del ticket,
- representa lineas del ticket,
- depende de la cabecera.

### 3.3 SAPRCTGDI
Tabla origen de **distribucion del ticket**.
Responsabilidades funcionales:
- contiene la lista de tiendas a las que aplica el ticket,
- soporta la seguridad de acceso por tienda,
- depende de la cabecera.

## 4. Llave unica natural del ticket
La llave natural que identifica al ticket en origen y relaciona las 3 tablas es:

```text
DGHTCK + DGHCOD + DGHSTR + DGHDAT
```

### Interpretacion dentro del nuevo sistema
En el nuevo sistema esos componentes se representan con nombres neutrales:

- `source_ticket_code`
- `source_business_code`
- `source_store_code`
- `source_ticket_date`

Y adicionalmente se genera una llave tecnica derivada:

- `source_ticket_key`

Formato sugerido:

```text
source_ticket_code|source_business_code|source_store_code|YYYYMMDD
```

Ejemplo:

```text
ABCD|01|1234|20260618
```

## 5. Alcance funcional del sistema

### 5.1 Dentro del alcance
El sistema debe incluir:

#### a) Integracion desde AS400
- lectura regular de lotes JSON generados en IFS;
- registro de lotes y archivos;
- parseo y persistencia en tablas inbound/staging;
- consolidacion hacia tablas operativas;
- control de duplicados logicos;
- bitacora de errores de integracion.

#### b) Consulta operativa de tickets
- consulta por ticket,
- consulta por tienda,
- consulta por fecha,
- consulta por estatus de origen,
- consulta por estatus documental del archivo,
- visualizacion de cabecera,
- visualizacion de detalle,
- visualizacion de distribucion.

#### c) Seguridad por rol y tienda
- usuario de tienda solo ve tickets de sus tiendas;
- supervisor ve cualquier ticket;
- administrador ve cualquier ticket y administra seguridad/configuracion.

#### d) Archivo escaneado
- subir archivo escaneado a nivel ticket;
- reemplazar archivo mientras no este confirmado;
- confirmar archivo;
- consultar/visualizar archivo confirmado o no confirmado;
- aplicar regla de estatus 9 de origen.

#### e) Auditoria
- auditoria de lotes,
- auditoria de carga/reemplazo/confirmacion de archivo,
- auditoria de eventos administrativos relevantes.

### 5.2 Fuera de alcance (por ahora)
- captura manual inicial del ticket;
- OCR del ticket escaneado;
- homologacion avanzada de productos;
- analitica avanzada de pricing;
- modificacion web del ticket de origen;
- integracion bidireccional para actualizar SAP/AS400;
- validacion documental posterior del escaneo.

## 6. Reglas funcionales cerradas

### 6.1 Regla de tickets nuevos
La integracion se asume **solo con tickets nuevos**.

Si un ticket ya existe en el nuevo sistema y por alguna razon vuelve a llegar desde origen:
- no se sustituye,
- no se sobreescribe,
- se registra como existente/repetido,
- el importador no debe duplicarlo.

### 6.2 Regla de entidad principal
La cabecera es la entidad principal del ticket.

- detalle y distribucion dependen de la cabecera,
- no debe existir detalle ni distribucion huerfana en el modelo operativo.

### 6.3 Regla de visibilidad por tienda
Un `STORE_USER` solo puede consultar tickets cuya distribucion contenga alguna tienda asignada a ese usuario.

### 6.4 Regla de acceso global
Los roles `SUPERVISOR` y `ADMIN` pueden consultar cualquier ticket.

### 6.5 Regla de estatus para adjuntar archivo
El archivo escaneado solo puede adjuntarse/reemplazarse si el ticket tiene:

```text
source_status_code = '9'
```

### 6.6 Regla de un solo archivo activo
Cada ticket puede tener historial de versiones del archivo escaneado, pero solo **una** version puede estar activa.

### 6.7 Regla de reemplazo antes de confirmacion
El archivo activo puede reemplazarse mientras:
- este activo,
- no este confirmado,
- el ticket siga cumpliendo la regla del estatus de origen.

### 6.8 Regla de bloqueo despues de confirmacion
Una version confirmada del archivo:
- no puede modificarse,
- no puede eliminarse,
- no puede reemplazarse,
- se conserva para consulta.

### 6.9 Regla de uso del archivo escaneado
El archivo escaneado se usa exclusivamente como **consulta/visualizacion** documental.
No requiere validacion posterior ni OCR en esta fase.

## 7. Roles del sistema

### 7.1 STORE_USER (usuario de tienda)
Puede:
- consultar tickets de sus tiendas;
- ver cabecera, detalle y distribucion de tickets autorizados;
- cargar archivo escaneado si el ticket esta en estatus 9;
- reemplazar archivo antes de confirmar;
- confirmar archivo;
- visualizar archivo.

No puede:
- ver tickets de otras tiendas;
- modificar informacion base del ticket;
- administrar usuarios;
- administrar lotes de manera tecnica.

### 7.2 SUPERVISOR
Puede:
- ver cualquier ticket;
- consultar cabecera, detalle, distribucion y archivo;
- monitorear tickets con/sin archivo;
- dar seguimiento global.

No necesariamente administra seguridad.

### 7.3 ADMIN
Puede:
- ver cualquier ticket;
- administrar usuarios;
- administrar roles;
- asignar tiendas a usuarios;
- monitorear interfaces y lotes;
- consultar auditoria;
- parametrizar elementos operativos si posteriormente se habilita.

## 8. Flujo funcional resumido

```text
SAP
 ↓
AS400
 ↓
SAPRCTGH / SAPRCTGD / SAPRCTGDI
 ↓
Programa RPG Free
 ↓
JSON en IFS
 ↓
Importador
 ↓
Base de datos del sistema web
 ↓
Consulta por usuario segun rol
 ↓
Adjunto/reemplazo/confirmacion del ticket escaneado
 ↓
Visualizacion del ticket escaneado
```

## 9. Decisiones tecnicas cerradas
- Formato de intercambio: `JSON`.
- Estructura de carpetas en IFS: una sola carpeta inbound + `ARCHIVE` (+ `ERROR` opcional).
- No se usaran carpetas por lote.
- Los archivos se identifican por timestamp en el nombre.
- Se prefiere PostgreSQL como motor minimo.
- Se preparo equivalente en SQL Server.

## 10. Criterios de aceptacion macro
El proyecto cumple si puede:
1. importar tickets nuevos desde AS400/IFS;
2. consolidar cabecera, detalle y distribucion;
3. impedir duplicidad por llave de negocio;
4. restringir visibilidad de tickets por tienda;
5. permitir archivo escaneado si status de origen = 9;
6. permitir reemplazo solo antes de confirmar;
7. bloquear reemplazo/modificacion despues de confirmar;
8. auditar eventos clave.
