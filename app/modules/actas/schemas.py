"""Actas · validación de entrada."""
from datetime import date
from types import SimpleNamespace
from app.core.errors import ApiError
from app.core.validation import texto


def _fecha(v, campo):
    try:
        return date.fromisoformat(v) if v else None
    except (TypeError, ValueError):
        raise ApiError(422, f"Revisa el campo «{campo}»: valor no válido")


def acta(d):
    ks = d.get("compromisos") or []
    if not isinstance(ks, list) or len(ks) > 20:
        raise ApiError(422, "Revisa los compromisos del acta")
    compromisos = []
    for k in ks:
        k = k if isinstance(k, dict) else {}
        if not any(str(k.get(c) or "").strip() for c in ("descripcion", "responsable", "fecha_limite")):
            continue  # fila vacía del formulario
        f = _fecha(k.get("fecha_limite"), "fecha límite")
        if not f:
            raise ApiError(422, "Cada compromiso necesita fecha límite")
        compromisos.append(SimpleNamespace(descripcion=texto(k, "descripcion", 3, 300).strip(),
                                           responsable=texto(k, "responsable", 3, 120).strip(), fecha_limite=f))
    return SimpleNamespace(fecha=_fecha(d.get("fecha"), "fecha"), temas=texto(d, "temas", 3, 3000).strip(), compromisos=compromisos)


def cumplido(d):
    if not isinstance(d.get("cumplido"), bool):
        raise ApiError(422, "Revisa el campo «cumplido»: valor no válido")
    return d["cumplido"]
