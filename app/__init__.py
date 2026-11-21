"""Fábrica de la aplicación: arma el monolito registrando cada módulo (Blueprint)."""
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from app.core.config import settings
from app.core.database import init_db
from app.core.errors import ApiError
from app.modules.actas.routes import bp as actas_bp
from app.modules.auth.routes import bp as auth_bp
from app.modules.catalogo.routes import bp as catalogo_bp
from app.modules.entregables.routes import bp as entregables_bp
from app.modules.evaluacion.routes import bp as evaluacion_bp
from app.modules.objetivos.routes import bp as objetivos_bp
from app.modules.proyectos.routes import bp as proyectos_bp
from app.modules.seguimiento.routes import bp as seguimiento_bp
from app.modules.usuarios.routes import bp as usuarios_bp

FRONT = Path(__file__).resolve().parents[2] / "frontend"
MODULES = (auth_bp, proyectos_bp, objetivos_bp, actas_bp, entregables_bp, seguimiento_bp,
           evaluacion_bp, catalogo_bp, usuarios_bp)


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = (settings.MAX_PDF_MB + 1) * 1024 * 1024
    CORS(app)
    for bp in MODULES:
        app.register_blueprint(bp)

    @app.errorhandler(ApiError)
    def api_error(e):
        return jsonify({"error": e.message}), e.status

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Ruta no encontrada"}), 404

    @app.errorhandler(405)
    def bad_method(_):
        return jsonify({"error": "Método no permitido"}), 405

    @app.errorhandler(413)
    def too_large(_):
        return jsonify({"error": f"El archivo supera {settings.MAX_PDF_MB} MB"}), 413

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"error": "Error interno del servidor"}), 500

    @app.get("/")
    def index():
        return send_from_directory(FRONT, "index.html")

    @app.get("/<path:p>")
    def static_files(p):
        return send_from_directory(FRONT, p)

    init_db()
    return app
