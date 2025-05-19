import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ─── 1) Make sure we can import your app ───────────────────────────────────────
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, project_root)

# ─── 2) Load your .env (so settings picks up DATABASE_URL & friends) ─────────
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(project_root, '.env'))

# ─── 3) Import your settings and metadata ────────────────────────────────────
from app.core.config import settings    # pydantic BaseSettings reading your .env
from app.db.base import Base           # the declarative_base()
import app.db.models                    # noqa: registers all models

# this is the Alembic Config object
config = context.config

# ─── 4) Override URL from .env via settings ──────────────────────────────────
# (this replaces whatever is in alembic.ini)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# ─── 5) Set up logging ───────────────────────────────────────────────────────
fileConfig(config.config_file_name)

# ─── 6) Point Alembic at your MetaData ──────────────────────────────────────
target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"}
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
