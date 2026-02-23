import os
import sys
from dotenv import load_dotenv

# 1. Load from .env file (for local development)
load_dotenv()

GEMINI_API_KEY = None

# 2. Try Streamlit Secrets (for Cloud deployment)
try:
    import streamlit as st
    # streamlit.secrets behaves like a dict. .get() is safe.
    if hasattr(st, "secrets"):
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
except Exception:
    pass

# 3. Fallback to Environment Variables (if not in secrets)
if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# For debugging in console (optional, but helpful)
# print(f"DEBUG: GEMINI_API_KEY detected: {bool(GEMINI_API_KEY)}")

def validate_config():
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is missing.")
        return False
    return True
