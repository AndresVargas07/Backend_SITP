"""Catálogo · capa de rutas."""
from flask import Blueprint, jsonify
from app.core.errors import ApiError
from app.core.http import ADM, body
from app.core.validation import texto
from app.modules.auth.guard import auth
from app.modules.catalogo import service

bp = Blueprint("catalogo", __name__, url_prefix="/api")


@bp.get("/catalogos")
@auth()
def catalogos():
    return jsonify(service.catalogos())


@bp.post("/catalogos/<tipo>")
@auth(ADM)
def crear(tipo):
    return jsonify(service.crear(tipo, texto(body(), "nombre", 2, 80).strip())), 201


@bp.patch("/catalogos/<tipo>/<int:iid>")
@auth(ADM)
def actualizar(tipo, iid):
    d = body()
    activo = d.get("activo")
    if activo is not None and not isinstance(activo, bool):
        raise ApiError(422, "Revisa el campo «activo»: valor no válido")
    return jsonify(service.actualizar(tipo, iid, texto(d, "nombre", 0, 80).strip(), activo))
