"""Usuarios · capa de rutas (solo administrador)."""
from flask import Blueprint, g, jsonify
from app.core.http import ADM, body
from app.modules.auth.guard import auth
from app.modules.usuarios import repository, schemas, service

bp = Blueprint("usuarios", __name__, url_prefix="/api/admin")


@bp.get("/usuarios")
@auth(ADM)
def usuarios():
    return jsonify(repository.usuarios())


@bp.post("/usuarios")
@auth(ADM)
def crear():
    return jsonify(service.crear(schemas.nuevo(body()))), 201


@bp.patch("/usuarios/<int:uid>")
@auth(ADM)
def actualizar(uid):
    return jsonify(service.actualizar(g.user, uid, schemas.cambios(body())))


@bp.delete("/usuarios/<int:uid>")
@auth(ADM)
def eliminar(uid):
    return jsonify(service.eliminar(g.user, uid))


@bp.patch("/proyectos/<int:pid>/asignacion")
@auth(ADM)
def asignar(pid):
    return jsonify(service.asignar(g.user, pid, schemas.asignacion(body())))
