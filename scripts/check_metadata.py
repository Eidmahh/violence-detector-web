# scripts/check_metadata.py
import os, sys

# ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.base import Base      # your declarative_base()
import app.db.models               # MUST register User+Alert

print("Tables registered on Base.metadata:", list(Base.metadata.tables.keys()))
