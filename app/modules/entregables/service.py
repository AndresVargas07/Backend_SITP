"""Entregables · capa de negocio: subida de PDF por el estudiante y revisiones de los asesores."""
from datetime import datetime
from app.core.errors import ApiError
from app.core.http import EST, MET, TEC
from app.modules.actas.repository import acta as get_acta
from app.modules.catalogo import repository as catalogo
from app.modules.entregables import repository as repo, storage
from app.modules.proyectos.service import abierto, accesible
from app.modules.seguimiento.repository import registrar


def subir(user, pid, data, file):
    """Cada carga del estudiante es una nueva versión del entregable de la materia actual."""
    p = accesible(user, pid, EST)
    abierto(p)
    d = catalogo.entregable_def(data.defId) if data.defId else None
    if not d or d["curso"] != p["cursoActual"]:
        raise ApiError(422, "Selecciona un entregable de la materia actual")
    v = repo.next_version(pid, d["id"])
    rel = storage.save_entrega(file, p, d, v)
    eid = repo.insert_entregable(pid, d["id"], d["curso"], v, rel, data.descripcion.strip(), user["id"])
    nombre = rel.split("/")[-1]
    registrar(p, user, "Entregable", f"{d['codigo']} · {d['nombre']} (v{v}) subido como {nombre}")
    return {"id": eid, "version": v, "archivo": nombre}


def _entregable(eid):
    e = repo.entregable(eid)
    if not e:
        raise ApiError(404, "Entregable no encontrado")
    return e


def archivo_entregable(user, eid):
    e = _entregable(eid)
    accesible(user, e["proyectoId"])
    return storage.full_path(e["archivo"])


def archivo_revision(user, rid):
    r = repo.revision(rid)
    if not r or not r["pdf"]:
        raise ApiError(404, "Esta revisión no tiene PDF de observaciones")
    accesible(user, r["proyectoId"])
    return storage.full_path(r["pdf"])


def revisar(user, eid, data):
    """El técnico no califica: comenta y, si hay observaciones, se genera un PDF.
    El metodológico asigna estado y nota. Ambas quedan vinculadas al acta elegida."""
    e = _entregable(eid)
    p = accesible(user, e["proyectoId"], TEC, MET)
    abierto(p)
    acta = get_acta(data.actaId) if data.actaId else None
    if data.actaId and (not acta or acta["proyecto_id"] != p["id"]):
        raise ApiError(422, "El acta no pertenece a este proyecto")
    obs, corr = data.observaciones.strip(), data.correcciones.strip()
    tecnica = p["miRol"] == TEC
    if tecnica:
        estado, nota = ("Para corrección" if corr else "Revisado"), None
    else:
        estado, nota = data.estado, data.nota
        if not estado:
            raise ApiError(422, "Selecciona el estado del entregable")
    rid = repo.insert_revision(eid, p["id"], acta["id"] if acta else None, "tecnica" if tecnica else "metodologica",
                               estado, nota, obs, corr, user["id"])
    if tecnica and (obs or corr):
        materia = catalogo.materias()[e["curso"]]
        repo.set_revision_pdf(rid, storage.observaciones_pdf(rid, p, materia, e, acta, user, obs, corr,
                                                             datetime.now().strftime("%Y-%m-%d %H:%M")))
    if not (tecnica and e["estado"] == "Aprobado"):  # el técnico no reabre un entregable ya aprobado
        repo.update_estado(eid, estado, nota, set_nota=not tecnica)
    quien = "Revisión técnica" if tecnica else "Revisión metodológica"
    registrar(p, user, "Cambio de estado", f"{quien} de {e['codigo']} · {e['titulo']} (v{e['version']}): {estado}"
              + (f" — nota {nota:.1f}" if nota is not None else "") + (f" · Acta N.º {acta['numero']:02d}" if acta else ""))
    return {"id": rid, "estado": estado}
