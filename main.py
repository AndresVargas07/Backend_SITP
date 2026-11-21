"""Punto de entrada: python main.py  (abre http://localhost:8000)."""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
