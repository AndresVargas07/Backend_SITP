"""Catálogo · materias (los tres cursos), programas, semestres, entregables definidos y criterios de la rúbrica."""
from app.core.database import execute, fetch_all, fetch_one
from app.core.serializers import row, rows

TABLAS = ("programas", "semestres")  # catálogos que el administrador puede ampliar


def materias():
    return {r["id"]: r["nombre"] for r in fetch_all("SELECT id, nombre FROM materias ORDER BY id")}


def entregables_def():
    return rows(fetch_all("SELECT id, materia_id AS curso, codigo, nombre FROM entregables_def ORDER BY materia_id, codigo"))


def entregable_def(did):
    return row(fetch_one("SELECT id, materia_id AS curso, codigo, nombre FROM entregables_def WHERE id = %s", (did,)))


def criterios():
    return rows(fetch_all("SELECT * FROM criterios ORDER BY id"))


def lista(tabla):
    return rows(fetch_all(f"SELECT * FROM {tabla} ORDER BY nombre"))


def nombres(tabla):
    return [r["nombre"] for r in fetch_all(f"SELECT nombre FROM {tabla} WHERE activo = 1 ORDER BY nombre")]


def item(tabla, iid):
    return fetch_one(f"SELECT * FROM {tabla} WHERE id = %s", (iid,))


def existe(tabla, nombre, excepto=0):
    return fetch_one(f"SELECT id FROM {tabla} WHERE LOWER(nombre) = LOWER(%s) AND id <> %s", (nombre, excepto))


def crear(tabla, nombre):
    return execute(f"INSERT INTO {tabla} (nombre) VALUES (%s)", (nombre,))


def actualizar(tabla, iid, nombre=None, activo=None):
    if nombre is not None:
        execute(f"UPDATE {tabla} SET nombre = %s WHERE id = %s", (nombre, iid))
    if activo is not None:
        execute(f"UPDATE {tabla} SET activo = %s WHERE id = %s", (1 if activo else 0, iid))
