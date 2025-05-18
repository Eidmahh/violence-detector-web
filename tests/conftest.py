# tests/conftest.py
import os
import sys

# Add the project root to PYTHONPATH so pytest can import app/…
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
