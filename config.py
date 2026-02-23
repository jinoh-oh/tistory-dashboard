import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Gemini Config
try:
    import streamlit as st
    # Try loading from Streamlit secrets first (for Cloud)
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
except (ImportError, FileNotFoundError):
    GEMINI_API_KEY = None

# If not found in secrets, fallback to environment variable (for Local)
if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def validate_config():
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        print("Please check your .env file.")
        sys.exit(1)
