"""Auth · capa de datos: usuarios y sesiones."""
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.database import execute, fetch_all, fetch_one


def user_by_email(email):
    return fetch_one("SELECT * FROM usuarios WHERE LOWER(email) = LOWER(%s)", (email,))


def user_roles(uid):
    rows = fetch_all("SELECT rol FROM usuario_roles WHERE usuario_id = %s", (uid,))
    return [r["rol"] for r in rows] if rows else []


def user_by_id(uid):
    r = fetch_one("SELECT id, nombre, email, rol, programa, activo FROM usuarios WHERE id = %s", (uid,))
    if not r:
        return None
    u = dict(r)
    u["roles"] = user_roles(uid)
    return u


def create_session(token, uid, rol_activo=None):
    execute("DELETE FROM sesiones WHERE expira < NOW()")
    execute("INSERT INTO sesiones (token, usuario_id, expira, rol_activo) VALUES (%s, %s, %s, %s)",
            (token, uid, datetime.now() + timedelta(hours=settings.SESSION_HOURS), rol_activo))


def set_session_rol(token, rol_activo):
    execute("UPDATE sesiones SET rol_activo = %s WHERE token = %s", (rol_activo, token))


def user_by_token(token):
    r = fetch_one("""SELECT u.id, u.nombre, u.email, u.rol, u.programa, u.activo, s.rol_activo FROM sesiones s
                     JOIN usuarios u ON u.id = s.usuario_id WHERE s.token = %s AND s.expira > NOW() AND u.activo = 1""", (token,))
    if not r:
        return None
    u = dict(r)
    u["roles"] = user_roles(u["id"])
    if not u["roles"] and u["rol"]:
        u["roles"] = [u["rol"]]
    if u.get("rol_activo") and (u["rol"] == "administrador" or u["rol_activo"] in u["roles"]):
        u["rol_efectivo"] = u["rol_activo"]
    else:
        u["rol_efectivo"] = u["roles"][0] if u["roles"] else u["rol"]
    return u


def delete_session(token):
    execute("DELETE FROM sesiones WHERE token = %s", (token,))
