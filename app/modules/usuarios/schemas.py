"""Usuarios · validación de entrada."""
import re
from types import SimpleNamespace
# pyrefly: ignore[missing-import]
from app.core.errors import ApiError
# pyrefly: ignore[missing-import]
from app.core.validation import opcion, opcional, texto

ALL_ROLES = {"estudiante", "docente", "administrador", "asesor_tecnico", "asesor_metodologico", "jurado"}


def _parse_roles(d):
    roles = d.get("roles")
    if isinstance(roles, str):
        roles = [roles]
    if not roles and "rol" in d:
        r = d.get("rol")
        roles = [r] if r else []
    if roles:
        invalid = [r for r in roles if r not in ALL_ROLES]
        if invalid:
            raise ApiError(422, f"Roles no válidos: {', '.join(invalid)}")
        return list(dict.fromkeys(roles))
    return None


def nuevo(d):
    email = texto(d, "email", 6, 120).strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", email):
        raise ApiError(422, "Revisa el campo «email»: correo no válido")
    roles = _parse_roles(d)
    if not roles:
        raise ApiError(422, "Debes asignar al menos un rol al usuario")
    return SimpleNamespace(
        nombre=texto(d, "nombre", 3, 120).strip(),
        email=email,
        roles=roles,
        rol=roles[0],
        programa=texto(d, "programa", 0, 80).strip() or None,
        password=texto(d, "password", 8, 64),
    )


def cambios(d):
    activo = d.get("activo")
    if activo is not None and not isinstance(activo, bool):
        raise ApiError(422, "Revisa el campo «activo»: valor no válido")
    roles = _parse_roles(d)
    nombre = texto(d, "nombre", 3, 120).strip() if "nombre" in d and d.get("nombre") else None
    email = texto(d, "email", 6, 120).strip().lower() if "email" in d and d.get("email") else None
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", email):
        raise ApiError(422, "Revisa el campo «email»: correo no válido")
    programa = texto(d, "programa", 0, 80).strip() or None if "programa" in d else None
    password = texto(d, "password", 8, 64) if "password" in d and d.get("password") else None

    if all(x is None for x in (activo, roles, nombre, email, programa, password)):
        raise ApiError(422, "No hay cambios para guardar")
    return SimpleNamespace(nombre=nombre, email=email, roles=roles, rol=roles[0] if roles else None,
                           programa=programa, activo=activo, password=password)


def asignacion(d):
    ids = [opcional(d, k, int, 1) for k in ("tecnico", "metodologico", "jurado")]
    if None in ids[:2]:
        raise ApiError(422, "El proyecto necesita asesor técnico y metodológico")
    if len(set(i for i in ids if i)) != len([i for i in ids if i]):
        raise ApiError(422, "Técnico, metodológico y jurado deben ser docentes distintos")
    return SimpleNamespace(tecnico=ids[0], metodologico=ids[1], jurado=ids[2])
