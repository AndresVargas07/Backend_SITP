"""Proyectos · capa de datos: resumen, acceso por rol y actualización."""
from app.core.database import execute, fetch_all, fetch_one
from app.core.http import rol_en
from app.core.serializers import row
from app.modules.auth.repository import user_by_id

_LAST = """FROM entregables e WHERE e.proyecto_id = p.id AND e.version = (SELECT MAX(e2.version) FROM entregables e2
    WHERE e2.proyecto_id = e.proyecto_id AND e2.def_id = e.def_id)"""
_SUMMARY = f"""
SELECT p.*,
  (SELECT COUNT(DISTINCT e.def_id) FROM entregables e WHERE e.proyecto_id = p.id) AS total_entregables,
  (SELECT COUNT(*) {_LAST} AND e.estado = 'Entregado') AS por_revisar,
  (SELECT COUNT(*) {_LAST} AND e.estado = 'Para corrección') AS para_correccion,
  (SELECT COUNT(*) FROM comentarios c WHERE c.proyecto_id = p.id) AS total_comentarios,
  (SELECT COUNT(*) FROM actas a WHERE a.proyecto_id = p.id) AS total_actas,
  (SELECT COUNT(*) FROM actas a WHERE a.proyecto_id = p.id AND a.firmada = 0) AS actas_sin_firma,
  (SELECT COUNT(*) FROM compromisos k JOIN actas a ON a.id = k.acta_id WHERE a.proyecto_id = p.id AND k.cumplido = 0) AS compromisos_pendientes,
  (SELECT ev.concepto FROM evaluaciones ev WHERE ev.proyecto_id = p.id AND ev.curso = p.curso_actual ORDER BY ev.fecha DESC LIMIT 1) AS concepto,
  GREATEST(p.creado,
    COALESCE((SELECT MAX(h.fecha) FROM historial h WHERE h.proyecto_id = p.id), p.creado),
    COALESCE((SELECT MAX(c.fecha) FROM comentarios c WHERE c.proyecto_id = p.id), p.creado)) AS ultima_actividad
FROM proyectos p
"""
_ACCESS = {  # %(u)s = id del usuario
    "estudiante": "p.id IN (SELECT proyecto_id FROM proyecto_estudiantes WHERE estudiante_id = %(u)s)",
    "asesor_tecnico": "p.asesor_tecnico_id = %(u)s",
    "asesor_metodologico": "p.asesor_metodologico_id = %(u)s",
    "jurado": "p.jurado_id = %(u)s",
    "docente": "%(u)s IN (p.asesor_tecnico_id, p.asesor_metodologico_id, p.jurado_id)",
    "administrador": "%(u)s IS NOT NULL",  # consulta global
}


def _access_condition(user):
    # Si el usuario es administrador (o rol_global es admin), acceso global sin filtrar por asignación
    if user.get("rol_global") == "administrador" or user.get("rol") == "administrador":
        return "%(u)s IS NOT NULL"
    rol_activo = user.get("rol_efectivo") or user.get("rol")
    return _ACCESS.get(rol_activo, "%(u)s IS NOT NULL")


def _with_people(p, user):
    est = fetch_all("""SELECT u.id, u.nombre, u.email, u.rol FROM proyecto_estudiantes pe
                       JOIN usuarios u ON u.id = pe.estudiante_id WHERE pe.proyecto_id = %s ORDER BY u.nombre""", (p["id"],))
    p["estudiantes"] = [e["id"] for e in est]
    p["estudiantesInfo"] = [dict(e) for e in est]
    p["asesorTecnico"] = user_by_id(p["asesorTecnicoId"])
    p["asesorMetodologico"] = user_by_id(p["asesorMetodologicoId"])
    p["jurado"] = user_by_id(p["juradoId"]) if p["juradoId"] else None
    p["miRol"] = rol_en(p, user)
    return p


def projects_for(user):
    cond = _access_condition(user)
    rs = fetch_all(_SUMMARY + f" WHERE {cond} ORDER BY ultima_actividad DESC", {"u": user["id"]})
    return [_with_people(row(r), user) for r in rs]


def project_for(user, pid):
    """Devuelve el proyecto solo si el usuario está vinculado (control de acceso en SQL)."""
    cond = _access_condition(user)
    r = fetch_one(_SUMMARY + f" WHERE p.id = %(pid)s AND {cond}", {"pid": pid, "u": user["id"]})
    return _with_people(row(r), user) if r else None


def project_exists(pid):
    return fetch_one("SELECT id FROM proyectos WHERE id = %s", (pid,)) is not None


def update_project(pid, curso=None, estado=None, titulo=None, grupo=None):
    """Promover de curso solo cambia la etapa activa: documentos, actas, objetivos y comentarios se conservan."""
    for col, v in (("titulo", titulo), ("grupo", grupo), ("curso_actual", curso), ("estado", estado)):
        if v is not None:
            execute(f"UPDATE proyectos SET {col} = %s WHERE id = %s", (v, pid))


def asignar(pid, tec, met, jur):
    execute("UPDATE proyectos SET asesor_tecnico_id = %s, asesor_metodologico_id = %s, jurado_id = %s WHERE id = %s", (tec, met, jur, pid))
