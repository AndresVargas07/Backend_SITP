"""Auth · capa de rutas: /api/auth/*."""
from flask import Blueprint, g, jsonify
from app.core.http import body
from app.modules.auth import schemas, service
from app.modules.auth.guard import auth

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    d = schemas.login(body())
    return jsonify(service.login(d.email, d.password))


@bp.get("/me")
@auth()
def me():
    return jsonify({"user": service.public_user(g.user)})


@bp.post("/switch-rol")
@auth()
def switch_rol():
    d = schemas.switch_rol(body())
    return jsonify(service.switch_rol(g.user, d.rol))


@bp.post("/logout")
@auth()
def logout():
    service.logout(g.user["token"])
    return jsonify({"ok": True})
