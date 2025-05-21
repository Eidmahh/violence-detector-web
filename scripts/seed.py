# scripts/seed.py

import sys, os

# 1) Ensure the project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 2) Import your ORM base, engine, models, and security utils
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.models import UserRole, User
from app.services.security import get_password_hash

# 3) Create any tables that don't yet exist
Base.metadata.create_all(bind=engine)

# 4) Open a session and seed the admin user
db = SessionLocal()
admin_email = "admin@example.com"
admin_pw    = "ChangeMe123!"

existing = db.query(User).filter_by(email=admin_email).first()
if existing:
    print("Admin user already exists:", admin_email)
else:
    hashed = get_password_hash(admin_pw)
    admin = User(
        email=admin_email,
        password_hash=hashed,
        role=UserRole.admin,
        is_active=True
    )
    db.add(admin)
    db.commit()
    print(f"Created admin user → {admin_email} / {admin_pw}")

db.close()