"""Auth · capa de negocio: inicio y cierre de sesión."""
import secrets
from app.core.errors import ApiError
from app.core.security import verify_password
from app.modules.auth import repository as repo


def public_user(u):
    out = {k: u.get(k) for k in ("id", "nombre", "email", "rol", "programa", "roles")}
    out["rolActivo"] = u.get("rol_efectivo") or u.get("rol_activo") or (u.get("roles")[0] if u.get("roles") else u.get("rol"))
    return out


def login(email, password):
    u = repo.user_by_email(email.strip())
    if not u or not verify_password(password, u["password_hash"]):
        raise ApiError(401, "Correo o contraseña incorrectos")
    if not u["activo"]:
        raise ApiError(403, "Tu cuenta está desactivada. Contacta al administrador")
    roles = repo.user_roles(u["id"])
    if not roles and u["rol"]:
        roles = [u["rol"]]
    rol_activo = roles[0] if roles else u["rol"]
    token = secrets.token_hex(32)
    repo.create_session(token, u["id"], rol_activo)
    u_full = {**u, "roles": roles, "rol_efectivo": rol_activo}
    return {"token": token, "user": public_user(u_full)}


def switch_rol(user, nuevo_rol):
    roles = user.get("roles") or []
    if user.get("rol") != "administrador" and nuevo_rol not in roles:
        raise ApiError(403, "No tienes ese rol asignado")
    repo.set_session_rol(user["token"], nuevo_rol)
    return {"rolActivo": nuevo_rol}


def logout(token):
    repo.delete_session(token)
