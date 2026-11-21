"""Evaluación · capa de negocio: el jurado califica con la rúbrica y emite un concepto."""
from app.core.errors import ApiError
from app.core.http import JUR
from app.modules.catalogo import repository as catalogo
from app.modules.evaluacion import repository as repo
from app.modules.evaluacion import schemas
from app.modules.proyectos.service import abierto, accesible
from app.modules.seguimiento.repository import registrar


def total(puntajes, criterios):
    """Promedio ponderado sobre 5 según el peso de cada criterio."""
    peso = sum(c["peso"] for c in criterios) or 1
    return round(sum(puntajes[str(c["id"])] * c["peso"] for c in criterios) / peso, 2)


def evaluar(user, pid, d):
    p = accesible(user, pid, JUR)
    abierto(p)
    cs = catalogo.criterios()
    data = schemas.evaluacion(d, cs)
    t = total(data.puntajes, cs)
    repo.guardar(pid, user["id"], p["cursoActual"], data.puntajes, t, data.concepto, data.observaciones)
    registrar(p, user, "Evaluación", f"Evaluación del jurado: {t:.2f}/5 · {data.concepto}")
    return {"total": t, "concepto": data.concepto}


def borrar(user, eid):
    e = repo.evaluacion(eid)
    if not e or e["juradoId"] != user["id"]:
        raise ApiError(404, "Evaluación no encontrada")
    p = accesible(user, e["proyectoId"], JUR)
    abierto(p)
    repo.borrar(eid)
    registrar(p, user, "Evaluación", "Evaluación del jurado eliminada")
    return {"ok": True}
