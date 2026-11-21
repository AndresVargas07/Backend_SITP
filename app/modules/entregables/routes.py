"""Entregables · capa de rutas."""
from flask import Blueprint, g, jsonify, request, send_file
from app.core.http import DOC, EST, body
from app.modules.auth.guard import auth
from app.modules.entregables import schemas, service

bp = Blueprint("entregables", __name__, url_prefix="/api")


@bp.post("/proyectos/<int:pid>/entregables")
@auth(EST)
def subir(pid):
    return jsonify(service.subir(g.user, pid, schemas.subida(request.form), request.files.get("archivo"))), 201


@bp.get("/entregables/<int:eid>/archivo")
@auth()
def archivo(eid):
    return send_file(service.archivo_entregable(g.user, eid), mimetype="application/pdf")


@bp.post("/entregables/<int:eid>/revisiones")
@auth(DOC)
def revisar(eid):
    return jsonify(service.revisar(g.user, eid, schemas.revision(body()))), 201


@bp.get("/revisiones/<int:rid>/pdf")
@auth()
def revision_pdf(rid):
    return send_file(service.archivo_revision(g.user, rid), mimetype="application/pdf")
