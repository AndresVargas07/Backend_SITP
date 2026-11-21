"""Validadores de entrada reutilizables por todos los módulos (sin librerías extra)."""
from app.core.errors import ApiError


def texto(d, k, mn=0, mx=1000, default=""):
    v = d.get(k, default)
    v = default if v is None else v
    if not isinstance(v, str) or not (mn <= len(v.strip()) and len(v) <= mx):
        raise ApiError(422, f"Revisa el campo «{k}»: valor no válido")
    return v


def opcional(d, k, cast, lo=None, hi=None):
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


def opcion(d, k, options, default):
    v = d.get(k, default)
    if v not in options:
        raise ApiError(422, f"Revisa el campo «{k}»: valor no válido")
    return v
