"""Catálogo · capa de negocio: consulta para todos y administración para el rol administrador."""
from app.core.errors import ApiError
from app.modules.catalogo import repository as repo

EDITABLES = repo.TABLAS + ("materias",)  # las materias solo se renombran (son las 3 etapas fijas)


def catalogos():
    return {"programas": repo.lista("programas"), "semestres": repo.lista("semestres"), "materias": repo.lista("materias"),
            "entregables": repo.entregables_def(), "criterios": repo.criterios()}


def _tabla(tipo, editable=EDITABLES):
    if tipo not in editable:
        raise ApiError(404, "Catálogo no encontrado")
    return tipo


def _nombre(tabla, nombre, excepto=0):
    if repo.existe(tabla, nombre, excepto):
        raise ApiError(409, f"Ya existe «{nombre}» en el catálogo")
    return nombre


def crear(tipo, nombre):
    t = _tabla(tipo, repo.TABLAS)
    return {"id": repo.crear(t, _nombre(t, nombre))}


def actualizar(tipo, iid, nombre, activo):
    t = _tabla(tipo)
    if not repo.item(t, iid):
        raise ApiError(404, "Elemento no encontrado")
    if t == "materias" and activo is not None:
        raise ApiError(422, "Las materias son las tres etapas fijas; solo se pueden renombrar")
    repo.actualizar(t, iid, _nombre(t, nombre, iid) if nombre else None, activo)
    return {"ok": True}
