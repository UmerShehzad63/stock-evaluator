"""
Vercel serverless function entry point.
This file imports the FastAPI app from server/main.py
so Vercel can discover and serve it.
"""
import sys
import os

# Add the server directory to Python's path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from main import app
