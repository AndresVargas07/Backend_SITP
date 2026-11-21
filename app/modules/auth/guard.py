"""Auth · decorador @auth(...): exige sesión válida y controla el acceso por rol (RBAC)."""
from functools import wraps
from flask import g, request
from app.core.errors import ApiError
from app.modules.auth import repository as repo


def auth(*allowed):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            user = token and repo.user_by_token(token)
            if not user:
                raise ApiError(401, "Sesión no válida o expirada")
            rol_efectivo = user.get("rol_efectivo") or user["rol"]
            # Si el usuario es administrador global o el rol efectivo está en los permitidos
            if allowed and user["rol"] != "administrador" and rol_efectivo not in allowed:
                raise ApiError(403, "Tu rol no tiene permiso para esta acción")
            g.user = {**user, "token": token, "rol": rol_efectivo, "rol_global": user["rol"]}
            return fn(*a, **kw)
        return wrapper
    return deco
