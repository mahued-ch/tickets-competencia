
# Proyecto: Sistema Web de Gestion de Tickets de Competencia

## Objetivo de este paquete
Este paquete de documentacion en Markdown concentra **todo el conocimiento funcional, tecnico y operativo** definido para el proyecto de sustitucion del sistema tipo InvesDoc usado para tickets de competencia.

Esta documentacion esta redactada para que **otra IA o ID (Ingenieria de Desarrollo)** pueda:

1. Entender el problema de negocio.
2. Entender el flujo de integracion SAP -> AS400 -> IFS -> Sistema Web.
3. Entender el modelo de datos y las reglas de negocio.
4. Implementar la base de datos en PostgreSQL o SQL Server.
5. Implementar el importador de archivos JSON.
6. Implementar el modulo de consulta y el modulo de carga/confirmacion del ticket escaneado.
7. Respetar exactamente las restricciones del proyecto.

## Contexto de negocio
- El sistema sustituira la funcionalidad documental/operativa actualmente cubierta por InvesDoc para tickets de competencia.
- **La captura manual inicial del ticket NO es parte del alcance actual**.
- La informacion base del ticket **ya llega desde SAP** y se integra a tablas de AS400.
- El nuevo sistema web consumira esa informacion regularmente para construir una base propia de consulta y operacion.
- En una etapa posterior del flujo, usuarios de tienda podran **adjuntar el ticket escaneado** si la cabecera del ticket se encuentra en el estatus correcto.

## Fuente actual de datos en AS400
Tablas origen:

- `SAPRCTGH`: cabecera del ticket.
- `SAPRCTGD`: detalle/productos del ticket.
- `SAPRCTGDI`: distribucion del ticket (lista de tiendas a las que aplica).

## Llave de negocio del ticket en origen
La llave unica natural del ticket es la combinacion de estos campos origen:

- `DGHTCK`
- `DGHCOD`
- `DGHSTR`
- `DGHDAT`

Esta misma llave relaciona las 3 tablas origen.

## Regla principal de escaneo
- El ticket escaneado se adjunta **a nivel cabecera**.
- Solo se permite adjuntar si la cabecera del ticket tiene **estatus 9** en origen.
- Solo se maneja **un archivo activo por ticket**.
- El archivo puede **reemplazarse** mientras **no este confirmado**.
- Una vez confirmado, **ya no se puede modificar**.
- No hay validacion posterior del archivo: solo se usa para **consulta/visualizacion**.

## Estructura del paquete

### 1. Vision, alcance y reglas
- [01_VISION_ALCANCE_REGLAS.md](./01_VISION_ALCANCE_REGLAS.md)

### 2. Arquitectura, integracion JSON y proceso IFS
- [02_ARQUITECTURA_E_INTEGRACION_JSON.md](./02_ARQUITECTURA_E_INTEGRACION_JSON.md)

### 3. Modelo de datos (explicado)
- [03_MODELO_DE_DATOS_DETALLADO.md](./03_MODELO_DE_DATOS_DETALLADO.md)

### 4. DDL completo PostgreSQL
- [04_DDL_POSTGRESQL.md](./04_DDL_POSTGRESQL.md)

### 5. DDL completo SQL Server
- [05_DDL_SQLSERVER.md](./05_DDL_SQLSERVER.md)

### 6. Funciones y flujo del archivo escaneado
- [06_FUNCIONES_POSTGRESQL_ARCHIVO_ESCANEADO.md](./06_FUNCIONES_POSTGRESQL_ARCHIVO_ESCANEADO.md)

### 7. Roles, seguridad y permisos funcionales
- [07_ROLES_SEGURIDAD_Y_OPERACION.md](./07_ROLES_SEGURIDAD_Y_OPERACION.md)

### 8. Guía de implementacion para otra IA/ID
- [08_GUIA_DE_IMPLEMENTACION_PARA_OTRA_IA.md](./08_GUIA_DE_IMPLEMENTACION_PARA_OTRA_IA.md)

## Orden recomendado de lectura
1. `01_VISION_ALCANCE_REGLAS.md`
2. `02_ARQUITECTURA_E_INTEGRACION_JSON.md`
3. `03_MODELO_DE_DATOS_DETALLADO.md`
4. `06_FUNCIONES_POSTGRESQL_ARCHIVO_ESCANEADO.md`
5. `07_ROLES_SEGURIDAD_Y_OPERACION.md`
6. `04_DDL_POSTGRESQL.md`
7. `05_DDL_SQLSERVER.md`
8. `08_GUIA_DE_IMPLEMENTACION_PARA_OTRA_IA.md`

## Decisiones tecnicas ya cerradas
- Motor minimo recomendado: **PostgreSQL**.
- Se mantiene equivalencia conceptual para **SQL Server**.
- Formato de intercambio: **JSON**.
- No se usaran carpetas por lote en IFS.
- Se usara **una sola carpeta inbound** con archivos nombrados por timestamp.
- Los archivos procesados se moveran a `ARCHIVE` (y opcionalmente `ERROR`).
- El lote se identifica logicamente por el timestamp compartido del nombre de archivo.
- El sistema operativo del ticket no reemplaza tickets ya integrados: el importador es **insert-only** respecto al ticket de origen.

## Convencion de nombres del lote en IFS
Archivos esperados por corrida:

```text
header_YYYYMMDD_HHMMSS.json
items_YYYYMMDD_HHMMSS.json
stores_YYYYMMDD_HHMMSS.json
control_YYYYMMDD_HHMMSS.json
```

Ejemplo:

```text
header_20260618_090000.json
items_20260618_090000.json
stores_20260618_090000.json
control_20260618_090000.json
```

## Regla operativa clave del importador
El importador solo debe procesar un lote cuando exista el archivo:

```text
control_YYYYMMDD_HHMMSS.json
```

Ese archivo representa la senal de "lote completo".

## Resultado final esperado del proyecto
El sistema web debe permitir:
- importar y consolidar tickets desde AS400,
- consultar cabecera, detalle y distribucion,
- controlar visibilidad por tienda,
- adjuntar y confirmar ticket escaneado,
- auditar eventos,
- soportar crecimiento futuro.

## Nota para otra IA/ID
La fuente de verdad de las reglas de negocio de este proyecto es esta documentacion. En caso de duda:
1. priorizar el documento de vision y reglas,
2. despues el modelo de datos,
3. despues las funciones PostgreSQL,
4. despues el DDL.
