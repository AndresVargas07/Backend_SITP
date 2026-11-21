"""Seguimiento · capa de rutas."""
from flask import Blueprint, g, jsonify
from app.core.http import body
from app.modules.auth.guard import auth
from app.modules.seguimiento import schemas, service

bp = Blueprint("seguimiento", __name__, url_prefix="/api")


@bp.post("/proyectos/<int:pid>/comentarios")
@auth()
def comentario(pid):
    return jsonify(service.add_comentario(g.user, pid, schemas.comentario(body()))), 201
