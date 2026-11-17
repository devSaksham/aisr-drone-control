"""Pytest setup: make the controller package and the repo root importable."""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "controllers", "drone_main"))
sys.path.insert(0, ROOT)
