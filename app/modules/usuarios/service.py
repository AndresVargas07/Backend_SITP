"""Usuarios · capa de negocio: administración de cuentas, roles y asignación de docentes a proyectos."""
from app.core.errors import ApiError
from app.core.security import hash_password
from app.modules.proyectos import repository as proyectos
from app.modules.seguimiento.repository import registrar
from app.modules.usuarios import repository as repo


def crear(data):
    if repo.email_existe(data.email):
        raise ApiError(409, "Ya existe una cuenta con ese correo")
    return {"id": repo.crear(data.nombre, data.email, data.roles, data.programa, hash_password(data.password))}


def actualizar(admin, uid, data):
    u = repo.usuario(uid)
    if not u:
        raise ApiError(404, "Usuario no encontrado")
    if uid == admin["id"] and data.activo is False:
        raise ApiError(422, "No puedes desactivar tu propia cuenta")
    if data.email and repo.email_existe(data.email, exclude_id=uid):
        raise ApiError(409, "Ya existe otra cuenta con ese correo")
    pw_hash = hash_password(data.password) if data.password else None
    repo.actualizar(uid, nombre=data.nombre, email=data.email, roles=data.roles,
                    programa=data.programa, activo=data.activo, pw_hash=pw_hash)
    return {"ok": True}


def eliminar(admin, uid):
    u = repo.usuario(uid)
    if not u:
        raise ApiError(404, "Usuario no encontrado")
    if uid == admin["id"]:
        raise ApiError(422, "No puedes eliminar tu propia cuenta")
    repo.eliminar(uid)
    return {"ok": True}


def asignar(admin, pid, data):
    p = proyectos.project_for(admin, pid)
    if not p:
        raise ApiError(404, "Proyecto no encontrado")
    ids = [i for i in (data.tecnico, data.metodologico, data.jurado) if i]
    if len(repo.docentes_activos(ids)) != len(ids):
        raise ApiError(422, "Solo se pueden asignar docentes con cuenta activa")
    proyectos.asignar(pid, data.tecnico, data.metodologico, data.jurado)
    registrar(p, admin, "Asignación", "El administrador actualizó los docentes asignados al proyecto")
    return {"ok": True}
