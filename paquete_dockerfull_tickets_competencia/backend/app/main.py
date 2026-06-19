from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.api.routes.health import router as health_router
from app.api.routes.me import router as me_router
from app.api.routes.tickets import router as tickets_router
from app.api.routes.scan_file import router as scan_file_router
from app.api.routes.integration import router as integration_router
from app.api.routes.admin import router as admin_router
from app.api.routes.auth_route import router as auth_router
from app.api.routes.audit import router as audit_router

settings = get_settings()
configure_logging()

app = FastAPI(title=settings.app_name)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(health_router)
app.include_router(me_router)
app.include_router(tickets_router)
app.include_router(scan_file_router)
app.include_router(integration_router)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(audit_router)
