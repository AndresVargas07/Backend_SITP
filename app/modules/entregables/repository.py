"""Entregables · capa de datos: versiones de PDF y revisiones de los asesores."""
from app.core.database import execute, fetch_all, fetch_one
from app.core.serializers import AUTOR, row, rows

_ENT = f"""SELECT t.*, d.codigo, d.nombre AS titulo, {AUTOR} FROM entregables t
    JOIN entregables_def d ON d.id = t.def_id JOIN usuarios u ON u.id = t.autor_id"""


def entregables(pid):
    return rows(fetch_all(_ENT + " WHERE t.proyecto_id = %s ORDER BY t.fecha DESC, t.id DESC", (pid,)))


def entregable(eid):
    return row(fetch_one(_ENT + " WHERE t.id = %s", (eid,)))


def next_version(pid, did):
    return fetch_one("SELECT COALESCE(MAX(version), 0) + 1 AS n FROM entregables WHERE proyecto_id = %s AND def_id = %s", (pid, did))["n"]


def insert_entregable(pid, did, curso, version, archivo, descripcion, autor):
    return execute("""INSERT INTO entregables (proyecto_id, def_id, curso, version, archivo, descripcion, autor_id)
                      VALUES (%s,%s,%s,%s,%s,%s,%s)""", (pid, did, curso, version, archivo, descripcion, autor))


def update_estado(eid, estado, nota=None, set_nota=False):
    if set_nota:
        execute("UPDATE entregables SET estado = %s, nota = %s WHERE id = %s", (estado, nota, eid))
    else:
        execute("UPDATE entregables SET estado = %s WHERE id = %s", (estado, eid))


def revisiones(pid):
    return rows(fetch_all(f"""SELECT t.*, a.numero AS acta_numero, {AUTOR} FROM revisiones t JOIN usuarios u ON u.id = t.autor_id
        LEFT JOIN actas a ON a.id = t.acta_id WHERE t.proyecto_id = %s ORDER BY t.fecha DESC, t.id DESC""", (pid,)))


def revision(rid):
    return row(fetch_one("SELECT * FROM revisiones WHERE id = %s", (rid,)))


def insert_revision(eid, pid, acta_id, tipo, estado, nota, obs, corr, autor):
    return execute("""INSERT INTO revisiones (entregable_id, proyecto_id, acta_id, tipo, estado, nota, observaciones, correcciones, autor_id)
                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (eid, pid, acta_id, tipo, estado, nota, obs, corr, autor))


def set_revision_pdf(rid, path):
    execute("UPDATE revisiones SET pdf = %s WHERE id = %s", (path, rid))
