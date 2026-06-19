from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.db.session import SessionLocal
from app.models.user import AppUser
from app.security.password import hash_password

db = SessionLocal()
try:
    users = db.query(AppUser).all()
    for u in users:
        pw = hash_password("demo123")
        u.password_hash = pw
        print(f"  {u.login_name}: set hash")
    db.commit()
    print("Done.")
finally:
    db.close()
