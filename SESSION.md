# Estado de la sesion - Tickets Competencia

## Fecha
2026-06-18

## Que se hizo
- [x] Extraido paquete dockerfull
- [x] Instalado PostgreSQL 17, creada DB `tickets_db` con usuario `tickets_user`
- [x] Creado entorno virtual Python e instaladas dependencias
- [x] Instaladas dependencias Node del frontend
- [x] Ejecutado bootstrap de BD: 11 tablas + usuarios demo
- [x] Agregado CORS middleware al backend
- [x] Creados datos JSON de prueba para el importador
- [x] Ejecutado importador: 8 tickets insertados
- [x] Inicializado git y subido a GitHub (mahued-ch/tickets-competencia)
- [x] Creados start.bat / stop.bat
- [x] Agregada columna `password_hash` a `app_user`
- [x] Creada autenticacion por password (`POST /api/v1/auth/login`) con tokens Bearer
- [x] Creado `PUT /api/v1/auth/password` para cambio de password propio
- [x] Creado `PUT /api/v1/admin/users/{id}/password` para admin resetea password de cualquier usuario
- [x] Creado `POST /api/v1/admin/users` para admin crea nuevos usuarios
- [x] Creado `DELETE /api/v1/admin/users/{id}/stores/{store}` para eliminar tienda asignada
- [x] Actualizado frontend: LoginPage con formulario usuario/contraseña, modal cambio password, CRUD usuarios en UsersPage
- [x] Backward compatibility mantenida con header `X-Demo-User`

## URL activas
- Frontend: http://localhost:5173/login
- Backend API: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## Usuarios demo
admin, supervisor, store_a, store_b (password: `demo123`)

## Pendiente / Proximo paso
- Continuar implementacion segun documentacion en ai-context/
