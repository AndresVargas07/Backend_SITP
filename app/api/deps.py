"""Autenticación por token y control de acceso por rol (RBAC) con decoradores de Flask."""
from functools import wraps
from flask import request, g
from app.errors import ApiError
from app.repositories import repo


def auth(*allowed):
    """Exige sesión válida y, si se indican roles, que el usuario tenga uno de ellos.
    Usa rol_efectivo (el elegido con el Role Switcher) para el control de acceso.
    El administrador siempre tiene acceso total."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            user = token and repo.user_by_token(token)
            if not user:
                raise ApiError(401, "Sesión no válida o expirada")
            rol_efectivo = user.get("rol_efectivo") or user["rol"]
            # El administrador tiene acceso global (nunca bloqueado por rol)
            if allowed and rol_efectivo != "administrador" and rol_efectivo not in allowed:
                raise ApiError(403, "Tu rol no tiene permiso para esta acción")
            g.user = {**user, "token": token, "rol": rol_efectivo}
            return fn(*a, **kw)
        return wrapper
    return deco
