
# Guia de Implementacion para Otra IA / ID

## 1. Objetivo
Esta guia explica **como ejecutar el proyecto de punta a punta** con base en todas las decisiones tomadas.

El lector ideal es:
- otra IA enfocada en desarrollo,
- un equipo de Ingenieria de Desarrollo,
- un integrador backend/database,
- un responsable tecnico que continura el trabajo.

## 2. Principios que NO se deben romper

1. **No hay captura manual inicial del ticket.**
2. **La fuente del ticket es AS400.**
3. **La llave natural del ticket es DGHTCK + DGHCOD + DGHSTR + DGHDAT.**
4. **El sistema solo integra tickets nuevos.**
5. **No se sustituyen tickets ya integrados.**
6. **El archivo escaneado solo se permite si el ticket tiene source_status_code = '9'.**
7. **Solo existe un archivo activo por ticket.**
8. **El archivo puede reemplazarse solo antes de confirmar.**
9. **Un archivo confirmado ya no puede modificarse/reemplazarse.**
10. **La visibilidad de STORE_USER depende de las tiendas asignadas.**

## 3. Orden recomendado de construccion

### Fase 1. Base de datos
1. ejecutar DDL PostgreSQL;
2. crear usuarios tecnicos;
3. verificar catalogo de roles;
4. probar constraints e indices.

### Fase 2. Integrador JSON
1. construir lector de carpeta inbound;
2. detectar lotes por `control_*.json`;
3. registrar batch/files;
4. cargar staging;
5. consolidar a operativa;
6. mover a `ARCHIVE` o `ERROR`.

### Fase 3. Backend/API
1. autenticacion;
2. construccion de servicios de consulta;
3. filtros por rol/tienda;
4. endpoints de archivo escaneado;
5. dashboard de lotes y errores.

### Fase 4. Frontend
1. login;
2. consulta de tickets;
3. detalle del ticket;
4. carga/reemplazo/confirmacion de archivo;
5. administracion de usuarios/tiendas;
6. monitoreo de lotes.

### Fase 5. Pruebas integrales
1. lote feliz;
2. lote incompleto;
3. ticket duplicado;
4. seguridad por tienda;
5. carga de archivo en estatus 9;
6. bloqueo por archivo confirmado;
7. concurrencia basica en reemplazo/confirmacion.

## 4. Contratos minimos del backend

## 4.1 Consultas sugeridas

### Buscar tickets
Filtros sugeridos:
- `source_ticket_key`
- fecha inicial/final
- tienda
- `source_status_code`
- `scan_status`
- `has_scan_file`
- lote

### Obtener detalle de ticket
Debe devolver:
- cabecera (`ticket`)
- items (`ticket_item`)
- stores (`ticket_store`)
- archivo activo (`ticket_scan_file` activo)

## 4.2 Operaciones del archivo escaneado

### Subir o reemplazar archivo
Backend debe:
1. validar autenticacion;
2. validar permisos por rol/tienda;
3. guardar archivo fisico;
4. llamar `fn_replace_ticket_scan_file`;
5. responder con nueva version y metadata.

### Confirmar archivo
Backend debe:
1. validar autenticacion;
2. validar permisos por rol/tienda;
3. llamar `fn_confirm_ticket_scan_file`;
4. responder con metadata de confirmacion.

## 5. Estrategia de importador

### 5.1 Algoritmo recomendado
1. listar `control_*.json`;
2. por cada control, derivar `batch_code`;
3. validar archivos complementarios (`header/items/stores`);
4. registrar `integration_batch`;
5. registrar `integration_file`;
6. leer y validar JSON;
7. insertar en inbound;
8. consolidar tickets no existentes;
9. actualizar estadisticas del lote;
10. mover archivos a `ARCHIVE` o `ERROR`.

### 5.2 Consolidacion a tablas operativas
Para cada cabecera:
- buscar si ya existe ticket por `source_ticket_key`;
- si existe: omitir cabecera y sus dependientes;
- si no existe: insertar cabecera, items y stores.

## 6. Estructura de almacenamiento de archivos escaneados
El modelo guarda solo metadata del archivo en BD. El archivo fisico puede vivir en:
- IFS,
- shared path,
- almacenamiento de objetos,
- file server.

### Campos relevantes
- `storage_path`
- `storage_provider`
- `file_hash`

### Recomendacion
Mantener `file_hash` para trazabilidad y deteccion de repetidos si posteriormente se quiere ampliar.

## 7. Checklist tecnico por componente

## 7.1 RPG Free
- [ ] lee SAPRCTGH/SAPRCTGD/SAPRCTGDI
- [ ] convierte a JSON
- [ ] escribe `header/items/stores`
- [ ] escribe `control` al final
- [ ] respeta localizacion y formato de fecha acordado

## 7.2 Importador
- [ ] detecta lotes por timestamp en nombre
- [ ] valida lote completo
- [ ] registra tablas de integracion
- [ ] inserta staging
- [ ] consolida tickets nuevos
- [ ] maneja `ARCHIVE/ERROR`
- [ ] registra errores

## 7.3 Base de datos
- [ ] DDL desplegado
- [ ] funciones de archivo escaneado desplegadas
- [ ] vistas desplegadas
- [ ] indices verificados

## 7.4 Backend
- [ ] seguridad por rol
- [ ] seguridad por tienda
- [ ] consultas de ticket
- [ ] endpoints de archivo escaneado
- [ ] endpoints de monitoreo de lotes

## 7.5 Frontend
- [ ] login
- [ ] buscador de tickets
- [ ] detalle del ticket
- [ ] carga/reemplazo de archivo
- [ ] confirmacion de archivo
- [ ] visualizacion del archivo
- [ ] usuarios/tiendas (admin)

## 8. Casos de prueba minimos obligatorios

### Integracion
- lote completo feliz;
- falta `control.json`;
- falta `header/items/stores`;
- JSON invalido;
- ticket duplicado;
- detalle sin cabecera;
- distribucion sin cabecera.

### Seguridad
- STORE_USER solo ve sus tiendas;
- SUPERVISOR ve todo;
- ADMIN ve todo y administra.

### Escaneo
- subir archivo con status 9;
- intentar subir con status distinto de 9;
- reemplazar archivo no confirmado;
- confirmar archivo;
- intentar reemplazar confirmado;
- intentar eliminar/modificar confirmado.

## 9. Decisiones sugeridas de implementacion que quedaron abiertas (si se quiere profundizar)
Aunque el marco principal del proyecto esta definido, una IA/ID puede proponer detalles adicionales en estas areas sin romper las reglas base:
- tecnologia del frontend (React, Angular, etc.);
- tecnologia del backend (FastAPI, ASP.NET, Spring, etc.);
- mecanismo de autenticacion (LDAP, AD, Entra ID, propio);
- tamano maximo permitido de archivo;
- extensiones permitidas (`pdf`, `jpg`, `jpeg`, `png`);
- politica fisica de purge/retencion de archivos.

## 10. Recomendacion final a otra IA/ID
Si vas a desarrollar el proyecto, procede en este orden:

1. **No cambies reglas de negocio sin validacion.**
2. **Monta primero la base de datos y pruebala.**
3. **Construye el importador antes del frontend.**
4. **Usa las funciones de BD para el archivo escaneado.**
5. **No hagas DML directo sobre `ticket_scan_file` desde la app.**
6. **Implementa seguridad por tienda desde el backend.**
7. **Audita todo evento relevante.**

## 11. Resultado final esperado
Otra IA/ID deberia poder tomar este paquete y construir:
- BD,
- importador,
- backend,
- frontend,
- flujo de archivo escaneado,
- seguridad,
- monitoreo,
conforme a lo definido en esta conversacion.
