import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ─── 1) Make sure we can import your app ───────────────────────────────────────
# Calculate project_root = parent of this file's folder (violence-detector-web/)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
# Prepend it to the PYTHONPATH so "import app" works
sys.path.insert(0, project_root)

# ─── 2) Import your settings and metadata ─────────────────────────────────────
from app.core.config import settings    # your DATABASE_URL, etc.
from app.db.base import Base           # the declarative_base()
import app.db.models                    # noqa: F401 – registers the User/Alert models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# ─── 3) (Optional) override the URL if you want to drive it from .env ───────
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# ─── 4) tell Alembic what our MetaData target is ─────────────────────────────
target_metadata = Base.metadata