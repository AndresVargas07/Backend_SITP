"""Objetivos · capa de negocio: cada cambio crea una nueva versión."""
from app.core.errors import ApiError
from app.core.http import EST, MET
from app.modules.objetivos import repository as repo
from app.modules.proyectos.service import accesible
from app.modules.seguimiento.repository import registrar


def add_version(user, pid, data):
    p = accesible(user, pid, EST, MET)
    oid = data.objetivoId
    if oid:
        o = repo.objetivo(oid)
        if not o or o["proyecto_id"] != pid:
            raise ApiError(400, "Objetivo inválido")
        tipo = o["tipo"]
    else:
        tipo = data.tipo
        oid = repo.insert_objetivo(pid, tipo)
    motivo = data.motivo.strip() or "Sin motivo indicado"
    v = repo.insert_version(oid, data.texto.strip(), motivo, p["cursoActual"], user["id"])
    registrar(p, user, "Objetivo", f"Objetivo {tipo.lower()} versión {v}: {motivo}")
    return {"id": oid, "version": v}
