"""Configuración por variables de entorno (valores por defecto para desarrollo local)."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]  # carpeta backend/
load_dotenv(BASE_DIR / ".env")  # lee backend/.env si existe


class Settings:
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "sitp_ucc")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
    MAX_PDF_MB = int(os.getenv("MAX_PDF_MB", "10"))
    SESSION_HOURS = int(os.getenv("SESSION_HOURS", "8"))


settings = Settings()
