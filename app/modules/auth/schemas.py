"""Auth · validación de entrada."""
from types import SimpleNamespace
from app.core.errors import ApiError
from app.core.validation import texto

ROLES_PERMITIDOS = ("estudiante", "docente", "administrador", "asesor_tecnico", "asesor_metodologico", "jurado")


def login(d):
    return SimpleNamespace(email=texto(d, "email", 3, 160), password=texto(d, "password", 1, 200))


def switch_rol(d):
    r = d.get("rol", "")
    if r not in ROLES_PERMITIDOS:
        raise ApiError(422, "Rol no válido")
    return SimpleNamespace(rol=r)
