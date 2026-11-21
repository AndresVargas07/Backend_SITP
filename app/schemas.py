"""Validadores de entrada (sin librerías extra): devuelven un objeto con los campos limpios."""
from datetime import date
from types import SimpleNamespace
from app.errors import ApiError


_ALL_ROLES = {"estudiante", "docente", "administrador", "asesor_tecnico", "asesor_metodologico", "jurado"}


def _txt(d, k, mn=0, mx=1000, default=""):
    v = d.get(k, default)
    v = default if v is None else v
    if not isinstance(v, str) or not (mn <= len(v.strip()) and len(v) <= mx):
        raise ApiError(422, f"Revisa el campo «{k}»: valor no válido")
    return v


def _opt(d, k, cast, lo=None, hi=None):
    v = d.get(k)
    if v in (None, ""):
        return None
    try:
        v = cast(v)
    except (TypeError, ValueError):
        raise ApiError(422, f"Revisa el campo «{k}»: valor no válido")
    if (lo is not None and v < lo) or (hi is not None and v > hi):
        raise ApiError(422, f"Revisa el campo «{k}»: valor fuera de rango")
    return v


def _in(d, k, options, default):
    v = d.get(k, default)
    if v not in options:
        raise ApiError(422, f"Revisa el campo «{k}»: valor no válido")
    return v


def login(d):
    return SimpleNamespace(email=_txt(d, "email", 3, 160), password=_txt(d, "password", 1, 200))


def objetivo(d):
    return SimpleNamespace(objetivoId=_opt(d, "objetivoId", int), tipo=_in(d, "tipo", ("General", "Específico"), "Específico"),
                           texto=_txt(d, "texto", 10, 1000), motivo=_txt(d, "motivo", 0, 300))


def acta(d):
    f = d.get("fecha")
    try:
        f = date.fromisoformat(f) if f else None
    except (TypeError, ValueError):
        raise ApiError(422, "Revisa el campo «fecha»: valor no válido")
    return SimpleNamespace(fecha=f, temas=_txt(d, "temas", 3, 3000), compromisos=_txt(d, "compromisos", 0, 3000))


def revision(d):
    return SimpleNamespace(actaId=_opt(d, "actaId", int), observaciones=_txt(d, "observaciones", 0, 4000), correcciones=_txt(d, "correcciones", 0, 4000),
                           estado=_in(d, "estado", (None, "", "Revisado", "Para corrección", "Aprobado"), None) or None, nota=_opt(d, "nota", float, 0, 5))


def proyecto(d):
    return SimpleNamespace(titulo=_txt(d, "titulo", 0, 255).strip(), grupo=_txt(d, "grupo", 0, 10).strip())


def cancelacion(d):
    return SimpleNamespace(motivo=_txt(d, "motivo", 5, 300).strip())


def comentario(d):
    return SimpleNamespace(sobre=_in(d, "sobre", ("proyecto", "entregable", "acta"), "proyecto"),
                           sobreId=_opt(d, "sobreId", int), texto=_txt(d, "texto", 1, 2000))


def _roles_list(d):
    """Valida y retorna la lista de roles del body. Acepta 'roles' (lista) o 'rol' (string legacy)."""
    roles = d.get("roles")
    if isinstance(roles, str):
        roles = [roles]
    if not roles:
        # fallback legacy
        r = d.get("rol")
        roles = [r] if r else []
    if not roles:
        raise ApiError(422, "Debes asignar al menos un rol")
    invalid = [r for r in roles if r not in _ALL_ROLES]
    if invalid:
        raise ApiError(422, f"Roles no válidos: {', '.join(invalid)}")
    return list(dict.fromkeys(roles))  # deduplica manteniendo orden


def crear_usuario(d):
    return SimpleNamespace(
        nombre=_txt(d, "nombre", 3, 120).strip(),
        email=_txt(d, "email", 3, 160).strip().lower(),
        password=_txt(d, "password", 8, 64),
        roles=_roles_list(d),
        programa=_txt(d, "programa", 0, 80).strip() or None,
    )


def editar_usuario(d):
    """Todos los campos son opcionales en el PATCH."""
    out = SimpleNamespace(
        nombre=_txt(d, "nombre", 0, 120).strip() or None if "nombre" in d else None,
        email=_txt(d, "email", 0, 160).strip().lower() or None if "email" in d else None,
        roles=_roles_list(d) if ("roles" in d or "rol" in d) else None,
        programa=_txt(d, "programa", 0, 80).strip() or None if "programa" in d else None,
        activo=bool(d["activo"]) if "activo" in d else None,
        password=_txt(d, "password", 8, 64) if "password" in d and d.get("password") else None,
    )
    return out


def switch_rol(d):
    r = d.get("rol", "")
    if r not in _ALL_ROLES:
        raise ApiError(422, "Rol no válido")
    return SimpleNamespace(rol=r)

