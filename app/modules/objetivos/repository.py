"""Objetivos · capa de datos: objetivos y sus versiones."""
from app.core.database import execute, fetch_all, fetch_one
from app.core.serializers import autor, rows


def objetivos(pid):
    objs = rows(fetch_all("SELECT * FROM objetivos WHERE proyecto_id = %s ORDER BY tipo = 'General' DESC, id", (pid,)))
    for o in objs:
        o["versiones"] = rows(fetch_all(f"""SELECT v.version AS v, v.texto, v.motivo, v.curso, v.fecha, v.autor_id, {autor(int(pid))}
            FROM objetivo_versiones v JOIN usuarios u ON u.id = v.autor_id WHERE v.objetivo_id = %s ORDER BY v.version""", (o["id"],)))
    return objs


def objetivo(oid):
    return fetch_one("SELECT * FROM objetivos WHERE id = %s", (oid,))


def insert_objetivo(pid, tipo):
    return execute("INSERT INTO objetivos (proyecto_id, tipo) VALUES (%s, %s)", (pid, tipo))


def insert_version(oid, texto, motivo, curso, autor):
    n = fetch_one("SELECT COALESCE(MAX(version), 0) + 1 AS n FROM objetivo_versiones WHERE objetivo_id = %s", (oid,))["n"]
    execute("INSERT INTO objetivo_versiones (objetivo_id, version, texto, motivo, curso, autor_id) VALUES (%s,%s,%s,%s,%s,%s)",
            (oid, n, texto, motivo, curso, autor))
    return n
