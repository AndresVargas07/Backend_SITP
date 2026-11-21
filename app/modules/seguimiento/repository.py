"""Seguimiento · capa de datos: comentarios e historial de movimientos."""
from app.core.database import execute, fetch_all
from app.core.serializers import AUTOR, rows


def _list(table, pid):
    return rows(fetch_all(f"SELECT t.*, {AUTOR} FROM {table} t JOIN usuarios u ON u.id = t.autor_id "
                          "WHERE t.proyecto_id = %s ORDER BY t.fecha DESC, t.id DESC", (pid,)))


def comentarios(pid):
    return _list("comentarios", pid)


def historial(pid):
    return _list("historial", pid)


def insert_comentario(pid, sobre, sobre_id, curso, autor, texto):
    return execute("INSERT INTO comentarios (proyecto_id, sobre, sobre_id, curso, autor_id, texto) VALUES (%s,%s,%s,%s,%s,%s)",
                   (pid, sobre, sobre_id, curso, autor, texto))


def recent_comments(pids, limit=8):
    if not pids:
        return []
    marks = ",".join(["%s"] * len(pids))
    return rows(fetch_all(f"""SELECT t.*, p.titulo AS proyecto, {AUTOR} FROM comentarios t
        JOIN usuarios u ON u.id = t.autor_id JOIN proyectos p ON p.id = t.proyecto_id
        WHERE t.proyecto_id IN ({marks}) ORDER BY t.fecha DESC, t.id DESC LIMIT {int(limit)}""", tuple(pids)))


def registrar(p, user, tipo, detalle):
    """Guarda un movimiento en el historial del proyecto (lo usan todos los módulos)."""
    execute("INSERT INTO historial (proyecto_id, curso, autor_id, tipo, detalle) VALUES (%s,%s,%s,%s,%s)",
            (p["id"], p["cursoActual"], user["id"], tipo, detalle))
