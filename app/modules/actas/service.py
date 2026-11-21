"""Actas · capa de negocio: registro, firma del metodológico y seguimiento de compromisos."""
from datetime import date
from app.core.errors import ApiError
from app.core.http import EST, MET, TEC
from app.modules.actas import repository as repo
from app.modules.proyectos.service import abierto, accesible
from app.modules.seguimiento.repository import registrar


def add_acta(user, pid, data):
    p = accesible(user, pid, TEC, MET)
    abierto(p)
    n = repo.insert_acta(pid, p["cursoActual"], data.fecha or date.today(), user["id"], data.temas, data.compromisos)
    registrar(p, user, "Acta", f"Acta N.º {n:02d} registrada con {len(data.compromisos)} compromiso(s)")
    return {"numero": n}


def firmar(user, aid):
    a = repo.acta(aid)
    if not a:
        raise ApiError(404, "Acta no encontrada")
    p = accesible(user, a["proyecto_id"], MET)
    if a["firmada"]:
        raise ApiError(409, "El acta ya está firmada")
    repo.firmar(aid, user["id"])
    registrar(p, user, "Firma de acta", f"Acta N.º {a['numero']:02d} validada y firmada")
    return {"ok": True}


def cumplir(user, cid, valor):
    k = repo.compromiso(cid)
    if not k:
        raise ApiError(404, "Compromiso no encontrado")
    p = accesible(user, k["proyecto_id"], EST, TEC, MET)
    abierto(p)
    repo.set_cumplido(cid, valor)
    registrar(p, user, "Compromiso", f"«{k['descripcion']}» marcado como {'cumplido' if valor else 'pendiente'}")
    return {"ok": True}
