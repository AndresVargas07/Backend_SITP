"""Evaluación · capa de datos: rúbrica del jurado."""
import json
from app.core.database import execute, fetch_all, fetch_one
from app.core.serializers import row, rows


def evaluaciones(pid):
    rs = rows(fetch_all("""SELECT e.*, u.nombre AS jurado FROM evaluaciones e JOIN usuarios u ON u.id = e.jurado_id
        WHERE e.proyecto_id = %s ORDER BY e.curso DESC, e.fecha DESC""", (pid,)))
    for e in rs:
        e["puntajes"] = json.loads(e["puntajes"])
        e["total"] = float(e["total"])
    return rs


def evaluacion(eid):
    return row(fetch_one("SELECT * FROM evaluaciones WHERE id = %s", (eid,)))


def guardar(pid, jurado, curso, puntajes, total, concepto, observaciones):
    execute("""INSERT INTO evaluaciones (proyecto_id, jurado_id, curso, puntajes, total, concepto, observaciones)
        VALUES (%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE puntajes = VALUES(puntajes), total = VALUES(total),
        concepto = VALUES(concepto), observaciones = VALUES(observaciones)""",
            (pid, jurado, curso, json.dumps(puntajes), total, concepto, observaciones))


def borrar(eid):
    execute("DELETE FROM evaluaciones WHERE id = %s", (eid,))
