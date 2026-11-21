"""Actas · capa de rutas."""
from flask import Blueprint, g, jsonify
from app.core.http import DOC, EST, body
from app.modules.actas import schemas, service
from app.modules.auth.guard import auth

bp = Blueprint("actas", __name__, url_prefix="/api")


@bp.post("/proyectos/<int:pid>/actas")
@auth(DOC)
def acta(pid):
    return jsonify(service.add_acta(g.user, pid, schemas.acta(body()))), 201


@bp.post("/actas/<int:aid>/firma")
@auth(DOC)
def firma(aid):
    return jsonify(service.firmar(g.user, aid))


@bp.patch("/compromisos/<int:cid>")
@auth(EST, DOC)
def compromiso(cid):
    return jsonify(service.cumplir(g.user, cid, schemas.cumplido(body())))
