"""Convierte filas SQL (snake_case) en JSON (camelCase) con el autor anidado."""
from datetime import date, datetime
from decimal import Decimal



def autor(pid="t.proyecto_id"):
    """Columnas del autor; si es docente, su rol se calcula según el proyecto (técnico, metodológico o jurado)."""
    return f"""u.id AS autor_id_, u.nombre AS autor_nombre, u.email AS autor_email,
      CASE WHEN u.rol <> 'docente' THEN u.rol ELSE (SELECT CASE WHEN px.asesor_tecnico_id = u.id THEN 'asesor_tecnico'
        WHEN px.asesor_metodologico_id = u.id THEN 'asesor_metodologico' WHEN px.jurado_id = u.id THEN 'jurado' ELSE 'docente' END
        FROM proyectos px WHERE px.id = {pid}) END AS autor_rol"""


AUTOR = autor()


def _val(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


def _camel(k):
    head, *rest = k.split("_")
    return head + "".join(w.capitalize() for w in rest)


def row(r):
    if r is None:
        return None
    out, autor = {}, {}
    for k, v in r.items():
        if k.startswith("autor_") and k != "autor_id":
            autor[k.removeprefix("autor_").rstrip("_") or "id"] = v
        else:
            out[_camel(k)] = _val(v)
    if autor:
        out["autor"] = {"id": autor.get("id"), "nombre": autor.get("nombre"), "email": autor.get("email"), "rol": autor.get("rol")}
    return out


def rows(rs):
    return [row(r) for r in rs]
