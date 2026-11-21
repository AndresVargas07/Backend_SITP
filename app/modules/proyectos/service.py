"""Proyectos · capa de negocio: panel, detalle, edición, cancelación y avance de materia.
Expone accesible() y abierto(), que los demás módulos usan para validar permisos."""
from app.core.errors import ApiError
from app.core.http import ADM, EST, JUR, MET
from app.modules.actas import repository as actas
from app.modules.catalogo import repository as catalogo
from app.modules.entregables import repository as entregables
from app.modules.evaluacion import repository as evaluacion
from app.modules.objetivos import repository as objetivos
from app.modules.proyectos import repository as repo
from app.modules.seguimiento import repository as seguimiento


def accesible(user, pid, *roles):
    """Devuelve el proyecto si el usuario está vinculado y, si se indican roles, si su rol EN ESTE proyecto es uno de ellos."""
    p = repo.project_for(user, pid)
    if not p:
        existe = repo.project_exists(pid)
        raise ApiError(403 if existe else 404, "No estás vinculado a este proyecto" if existe else "Proyecto no encontrado")
    if roles and p["miRol"] not in roles:
        raise ApiError(403, "Tu rol en este proyecto no permite esta acción")
    return p


def abierto(p):
    if p["estado"] != "En curso":
        raise ApiError(400, f"El proyecto está {p['estado'].lower()}; no admite cambios")


def _with_curso(p, cs):
    p["curso"] = cs[p["cursoActual"]]
    return p


def panel(user):
    cs = catalogo.materias()
    ps = [_with_curso(p, cs) for p in repo.projects_for(user)]
    return {"cursos": cs, "programas": catalogo.nombres("programas"), "proyectos": ps,
            "comentarios": seguimiento.recent_comments([p["id"] for p in ps])}


def detail(user, pid):
    cs = catalogo.materias()
    p = _with_curso(accesible(user, pid), cs)
    jurado = p["miRol"] in (JUR, ADM)  # la rúbrica solo la ven el jurado y el administrador
    return {**p, "cursos": cs, "catalogo": catalogo.entregables_def(), "objetivos": objetivos.objetivos(pid),
            "criterios": catalogo.criterios() if jurado else [], "evaluaciones": evaluacion.evaluaciones(pid) if jurado else [],
            "actas": actas.actas(pid), "entregables": entregables.entregables(pid), "revisiones": entregables.revisiones(pid),
            "comentarios": seguimiento.comentarios(pid), "historial": seguimiento.historial(pid)}


def editar(user, pid, data):
    p = accesible(user, pid, EST, MET)
    abierto(p)
    cambios = []
    if data.titulo and data.titulo != p["titulo"]:
        cambios.append(("Cambio de nombre", f"«{p['titulo']}» → «{data.titulo}»"))
    if data.grupo and data.grupo != p["grupo"] and p["miRol"] == MET:
        cambios.append(("Modificación", f"Grupo {p['grupo']} → {data.grupo}"))
    if not cambios:
        raise ApiError(422, "No hay cambios para guardar")
    repo.update_project(pid, titulo=data.titulo or None, grupo=data.grupo or None)
    for tipo, detalle in cambios:
        seguimiento.registrar(p, user, tipo, detalle)
    return {"ok": True}


def cancelar(user, pid, motivo):
    p = accesible(user, pid, MET)
    abierto(p)
    repo.update_project(pid, estado="Cancelado")
    seguimiento.registrar(p, user, "Cancelación", f"Proyecto cancelado. Motivo: {motivo}")
    return {"ok": True}


def avanzar(user, pid):
    p = accesible(user, pid, MET)
    abierto(p)
    cs = catalogo.materias()
    if p["cursoActual"] >= 3:
        repo.update_project(pid, estado="Finalizado")
        seguimiento.registrar(p, user, "Cierre", "Proyecto finalizado al terminar Aplicación Práctica del Trabajo de Grado")
    else:
        nuevo = p["cursoActual"] + 1
        repo.update_project(pid, curso=nuevo)
        seguimiento.registrar({**p, "cursoActual": nuevo}, user, "Cambio de curso",
                              f"El proyecto avanzó a {cs[nuevo]} conservando su historial completo.")
    return {"ok": True}
