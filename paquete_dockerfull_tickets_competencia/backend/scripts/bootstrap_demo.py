from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.db.base import Base
from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.models import AppRole, AppUser, AppUserStore
from app.security.password import hash_password


def main():
    engine.execute if False else None
    with engine.begin() as conn:
        conn.execute(text('CREATE SCHEMA IF NOT EXISTS competitor_ticket'))
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        roles = {
            'STORE_USER': 'Usuario de tienda',
            'SUPERVISOR': 'Supervisor',
            'ADMIN': 'Administrador',
        }
        role_rows = {}
        for code, name in roles.items():
            row = db.query(AppRole).filter(AppRole.role_code == code).first()
            if not row:
                row = AppRole(role_code=code, role_name=name, is_active=True)
                db.add(row)
                db.flush()
            role_rows[code] = row

        users = [
            ('admin', 'Administrador Demo', 'admin@example.com', 'ADMIN', []),
            ('supervisor', 'Supervisor Demo', 'supervisor@example.com', 'SUPERVISOR', []),
            ('store_a', 'Usuario Tienda A', 'storea@example.com', 'STORE_USER', ['0123', '0789']),
            ('store_b', 'Usuario Tienda B', 'storeb@example.com', 'STORE_USER', ['0456']),
        ]
        for login, display, email, role_code, stores in users:
            user = db.query(AppUser).filter(AppUser.login_name == login).first()
            if not user:
                user = AppUser(login_name=login, display_name=display, email=email, role_id=role_rows[role_code].role_id, is_active=True, password_hash=hash_password("demo123"))
                db.add(user)
                db.flush()
            else:
                if not user.password_hash:
                    user.password_hash = hash_password("demo123")
            for store in stores:
                existing = db.query(AppUserStore).filter(AppUserStore.user_id == user.user_id, AppUserStore.store_code == store).first()
                if not existing:
                    db.add(AppUserStore(user_id=user.user_id, store_code=store, is_active=True))
        db.commit()
        print('Bootstrap completado correctamente.')
        print('Usuarios demo: admin, supervisor, store_a, store_b')
    finally:
        db.close()


if __name__ == '__main__':
    main()
