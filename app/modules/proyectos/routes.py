"""Proyectos · capa de rutas."""
from flask import Blueprint, g, jsonify
from app.core.http import DOC, EST, body
from app.modules.auth.guard import auth
from app.modules.proyectos import schemas, service

bp = Blueprint("proyectos", __name__, url_prefix="/api")


@bp.get("/panel")
@auth()
def panel():
    return jsonify(service.panel(g.user))


@bp.get("/proyectos/<int:pid>")
@auth()
def proyecto(pid):
    return jsonify(service.detail(g.user, pid))


@bp.patch("/proyectos/<int:pid>")
@auth(EST, DOC)
def editar(pid):
    return jsonify(service.editar(g.user, pid, schemas.proyecto(body())))


@bp.post("/proyectos/<int:pid>/cancelar")
@auth(DOC)
def cancelar(pid):
    return jsonify(service.cancelar(g.user, pid, schemas.cancelacion(body()).motivo))


@bp.post("/proyectos/<int:pid>/avanzar")
@auth(DOC)
def avanzar(pid):
    return jsonify(service.avanzar(g.user, pid))
