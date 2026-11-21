"""Evaluación · capa de rutas."""
from flask import Blueprint, g, jsonify
from app.core.http import DOC, body
from app.modules.auth.guard import auth
from app.modules.evaluacion import service

bp = Blueprint("evaluacion", __name__, url_prefix="/api")


@bp.post("/proyectos/<int:pid>/evaluacion")
@auth(DOC)
def evaluar(pid):
    return jsonify(service.evaluar(g.user, pid, body()))


@bp.delete("/evaluaciones/<int:eid>")
@auth(DOC)
def borrar(eid):
    return jsonify(service.borrar(g.user, eid))
