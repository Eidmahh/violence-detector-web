# scripts/check_db.py

import os
import sys

# 1) Compute the project root (one level up from scripts/)
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir)
)
# 2) Add the project root to Python's module search path
sys.path.insert(0, project_root)

# Now imports from 'app' will work
from app.core.config import settings
from sqlalchemy import create_engine, inspect

print("→ Using DATABASE_URL:", settings.DATABASE_URL)

# Create the engine with echo=True so you can see SQL in stdout
engine = create_engine(settings.DATABASE_URL, echo=True)
inspector = inspect(engine)
print("→ Tables:", inspector.get_table_names())
