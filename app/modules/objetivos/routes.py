"""Objetivos · capa de rutas."""
from flask import Blueprint, g, jsonify
from app.core.http import DOC, EST, body
from app.modules.auth.guard import auth
from app.modules.objetivos import schemas, service

bp = Blueprint("objetivos", __name__, url_prefix="/api")


@bp.post("/proyectos/<int:pid>/objetivos")
@auth(EST, DOC)
def objetivo(pid):
    return jsonify(service.add_version(g.user, pid, schemas.objetivo(body()))), 201
