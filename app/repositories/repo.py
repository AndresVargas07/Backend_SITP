"""Capa de persistencia (Repository): todas las consultas SQL a MySQL viven aquí."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from app.db import fetch_all, fetch_one, execute
from app.config import settings

AUTOR = "u.id AS autor_id_, u.nombre AS autor_nombre, u.email AS autor_email, u.rol AS autor_rol"


def _val(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


def _camel(k):
    head, *rest = k.split("_")
    return head + "".join(w.capitalize() for w in rest)


def _row(r):
    """Convierte una fila SQL (snake_case) en un dict JSON (camelCase) con el autor anidado."""
    if r is None:
        return None
    out, autor = {}, {}
    for k, v in r.items():
        if k.startswith("autor_") and k != "autor_id":
            autor[k.removeprefix("autor_").rstrip("_") or "id"] = v
        else:
            out[_camel(k)] = _val(v)
    if autor:
        out["autor"] = {"id": autor.get("id"), "nombre": autor.get("nombre"), "email": autor.get("email"), "rol": autor.get("rol")}
    return out


def _rows(rs):
    return [_row(r) for r in rs]


# ---------- Usuarios y sesiones ----------
def user_by_email(email):
    return fetch_one("SELECT * FROM usuarios WHERE LOWER(email) = LOWER(%s) AND activo = 1", (email,))


def user_by_id(uid):
    r = fetch_one("SELECT id, nombre, email, rol, programa, activo FROM usuarios WHERE id = %s", (uid,))
    if not r:
        return None
    u = dict(r)
    u["roles"] = _user_roles(uid)
    return u


def _user_roles(uid):
    rows = fetch_all("SELECT rol FROM usuario_roles WHERE usuario_id = %s", (uid,))
    return [r["rol"] for r in rows] if rows else []


def create_session(token, uid, rol_activo=None):
    execute("DELETE FROM sesiones WHERE expira < NOW()")
    execute("INSERT INTO sesiones (token, usuario_id, expira, rol_activo) VALUES (%s, %s, %s, %s)",
            (token, uid, datetime.now() + timedelta(hours=settings.SESSION_HOURS), rol_activo))


def set_session_rol(token, rol_activo):
    execute("UPDATE sesiones SET rol_activo = %s WHERE token = %s", (rol_activo, token))


def user_by_token(token):
    r = fetch_one("""SELECT u.id, u.nombre, u.email, u.rol, u.programa, s.rol_activo FROM sesiones s
                     JOIN usuarios u ON u.id = s.usuario_id
                     WHERE s.token = %s AND s.expira > NOW() AND u.activo = 1""", (token,))
    if not r:
        return None
    u = dict(r)
    u["roles"] = _user_roles(u["id"])
    # Si hay rol_activo elegido y es válido, úsalo como rol efectivo
    if u.get("rol_activo") and u["rol_activo"] in u["roles"]:
        u["rol_efectivo"] = u["rol_activo"]
    else:
        # Rol efectivo = primer rol disponible o el rol legacy
        u["rol_efectivo"] = u["roles"][0] if u["roles"] else u["rol"]
    return u


def delete_session(token):
    execute("DELETE FROM sesiones WHERE token = %s", (token,))


# ---------- Admin: CRUD de usuarios ----------
_ALL_ROLES = ("estudiante", "docente", "administrador", "asesor_tecnico", "asesor_metodologico", "jurado")


def admin_all_users():
    rows = fetch_all("""
        SELECT u.id, u.nombre, u.email, u.rol, u.programa, u.activo,
               (SELECT COUNT(DISTINCT pe.proyecto_id) FROM proyecto_estudiantes pe WHERE pe.estudiante_id = u.id) +
               (SELECT COUNT(*) FROM proyectos p WHERE p.asesor_tecnico_id = u.id OR p.asesor_metodologico_id = u.id OR p.jurado_id = u.id) AS proyectos
        FROM usuarios u ORDER BY u.nombre
    """)
    result = []
    for r in rows:
        u = _row(r)
        u["roles"] = _user_roles(u["id"])
        result.append(u)
    return result


def admin_user_by_id(uid):
    r = fetch_one("""
        SELECT u.id, u.nombre, u.email, u.rol, u.programa, u.activo
        FROM usuarios u WHERE u.id = %s
    """, (uid,))
    if not r:
        return None
    u = _row(r)
    u["roles"] = _user_roles(uid)
    return u


def admin_create_user(nombre, email, password_hash, roles, programa):
    # Rol legacy: primer rol de la lista (para compatibilidad)
    rol_legacy = roles[0] if roles else "estudiante"
    uid = execute("INSERT INTO usuarios (nombre, email, rol, programa, password_hash) VALUES (%s,%s,%s,%s,%s)",
                  (nombre, email, rol_legacy, programa or None, password_hash))
    for r in roles:
        execute("INSERT INTO usuario_roles (usuario_id, rol) VALUES (%s,%s)", (uid, r))
    return uid


def admin_update_user(uid, nombre=None, email=None, roles=None, programa=None, activo=None, password_hash=None):
    sets, params = [], []
    if nombre is not None:
        sets.append("nombre = %s"); params.append(nombre)
    if email is not None:
        sets.append("email = %s"); params.append(email)
    if programa is not None:
        sets.append("programa = %s"); params.append(programa or None)
    if activo is not None:
        sets.append("activo = %s"); params.append(int(activo))
    if password_hash is not None:
        sets.append("password_hash = %s"); params.append(password_hash)
    if sets:
        # También actualizar rol legacy con el primero de los nuevos roles si se pasan
        if roles is not None and roles:
            sets.append("rol = %s"); params.append(roles[0])
        params.append(uid)
        execute(f"UPDATE usuarios SET {', '.join(sets)} WHERE id = %s", tuple(params))
    if roles is not None:
        execute("DELETE FROM usuario_roles WHERE usuario_id = %s", (uid,))
        for r in roles:
            execute("INSERT INTO usuario_roles (usuario_id, rol) VALUES (%s,%s)", (uid, r))


def admin_delete_user(uid):
    execute("DELETE FROM usuarios WHERE id = %s", (uid,))


# ---------- Proyectos ----------
_LAST = """FROM entregables e WHERE e.proyecto_id = p.id AND e.version = (SELECT MAX(e2.version) FROM entregables e2
    WHERE e2.proyecto_id = e.proyecto_id AND e2.def_id = e.def_id)"""
_SUMMARY = f"""
SELECT p.*,
  (SELECT COUNT(DISTINCT e.def_id) FROM entregables e WHERE e.proyecto_id = p.id) AS total_entregables,
  (SELECT COUNT(*) {_LAST} AND e.estado = 'Entregado') AS por_revisar,
  (SELECT COUNT(*) {_LAST} AND e.estado = 'Para corrección') AS para_correccion,
  (SELECT COUNT(*) FROM comentarios c WHERE c.proyecto_id = p.id) AS total_comentarios,
  (SELECT COUNT(*) FROM actas a WHERE a.proyecto_id = p.id) AS total_actas,
  GREATEST(p.creado,
    COALESCE((SELECT MAX(h.fecha) FROM historial h WHERE h.proyecto_id = p.id), p.creado),
    COALESCE((SELECT MAX(c.fecha) FROM comentarios c WHERE c.proyecto_id = p.id), p.creado)) AS ultima_actividad
FROM proyectos p
"""
_ACCESS = {
    "estudiante": "p.id IN (SELECT proyecto_id FROM proyecto_estudiantes WHERE estudiante_id = %s)",
    "asesor_tecnico": "p.asesor_tecnico_id = %s",
    "asesor_metodologico": "p.asesor_metodologico_id = %s",
    "jurado": "p.jurado_id = %s",
    # El administrador en modo swap de otro rol ve TODO sin filtrar por asignación propia
    "administrador": "1 = 1",
}


def _uid_for_access(user):
    """Retorna el id correcto para la consulta de acceso según rol efectivo."""
    return user["id"]


def _with_people(p):
    est = fetch_all("""SELECT u.id, u.nombre, u.email, u.rol FROM proyecto_estudiantes pe
                       JOIN usuarios u ON u.id = pe.estudiante_id WHERE pe.proyecto_id = %s ORDER BY u.nombre""", (p["id"],))
    p["estudiantes"] = [e["id"] for e in est]
    p["estudiantesInfo"] = [dict(e) for e in est]
    p["asesorTecnico"] = user_by_id(p["asesorTecnicoId"])
    p["asesorMetodologico"] = user_by_id(p["asesorMetodologicoId"])
    return p


def projects_for(user):
    rol = user.get("rol_efectivo") or user["rol"]
    cond = _ACCESS.get(rol, "1 = 1")
    if cond == "1 = 1":
        rs = fetch_all(_SUMMARY + " ORDER BY ultima_actividad DESC")
    else:
        rs = fetch_all(_SUMMARY + f" WHERE {cond} ORDER BY ultima_actividad DESC", (user["id"],))
    return [_with_people(_row(r)) for r in rs]


def project_for(user, pid):
    """Devuelve el proyecto solo si el usuario está vinculado (control de acceso en SQL).
    El administrador siempre tiene acceso global."""
    rol = user.get("rol_efectivo") or user["rol"]
    cond = _ACCESS.get(rol, "1 = 1")
    if cond == "1 = 1":
        r = fetch_one(_SUMMARY + " WHERE p.id = %s", (pid,))
    else:
        r = fetch_one(_SUMMARY + f" WHERE p.id = %s AND {cond}", (pid, user["id"]))
    return _with_people(_row(r)) if r else None


def project_exists(pid):
    return fetch_one("SELECT id FROM proyectos WHERE id = %s", (pid,)) is not None


def update_project(pid, curso=None, estado=None, titulo=None, grupo=None):
    for col, v in (("titulo", titulo), ("grupo", grupo)):
        if v is not None:
            execute(f"UPDATE proyectos SET {col} = %s WHERE id = %s", (v, pid))
    if curso is not None:
        execute("UPDATE proyectos SET curso_actual = %s WHERE id = %s", (curso, pid))
    if estado is not None:
        execute("UPDATE proyectos SET estado = %s WHERE id = %s", (estado, pid))


# ---------- Catálogo ----------
def materias():
    return {r["id"]: r["nombre"] for r in fetch_all("SELECT id, nombre FROM materias ORDER BY id")}


def entregables_def():
    return _rows(fetch_all("SELECT id, materia_id AS curso, codigo, nombre FROM entregables_def ORDER BY materia_id, codigo"))


def entregable_def(did):
    return _row(fetch_one("SELECT id, materia_id AS curso, codigo, nombre FROM entregables_def WHERE id = %s", (did,)))


# ---------- Objetivos ----------
def objetivos(pid):
    objs = _rows(fetch_all("SELECT * FROM objetivos WHERE proyecto_id = %s ORDER BY tipo = 'General' DESC, id", (pid,)))
    for o in objs:
        o["versiones"] = _rows(fetch_all(f"""SELECT v.version AS v, v.texto, v.motivo, v.curso, v.fecha, v.autor_id, {AUTOR}
            FROM objetivo_versiones v JOIN usuarios u ON u.id = v.autor_id WHERE v.objetivo_id = %s ORDER BY v.version""", (o["id"],)))
    return objs


def objetivo(oid):
    return fetch_one("SELECT * FROM objetivos WHERE id = %s", (oid,))


def insert_objetivo(pid, tipo):
    return execute("INSERT INTO objetivos (proyecto_id, tipo) VALUES (%s, %s)", (pid, tipo))


def insert_objetivo_version(oid, texto, motivo, curso, autor):
    n = fetch_one("SELECT COALESCE(MAX(version), 0) + 1 AS n FROM objetivo_versiones WHERE objetivo_id = %s", (oid,))["n"]
    execute("INSERT INTO objetivo_versiones (objetivo_id, version, texto, motivo, curso, autor_id) VALUES (%s,%s,%s,%s,%s,%s)",
            (oid, n, texto, motivo, curso, autor))
    return n


# ---------- Actas, entregables, comentarios, historial ----------
def _list(table, pid, order):
    return _rows(fetch_all(f"SELECT t.*, {AUTOR} FROM {table} t JOIN usuarios u ON u.id = t.autor_id WHERE t.proyecto_id = %s ORDER BY {order}", (pid,)))


def actas(pid):
    return _list("actas", pid, "t.numero DESC")


_ENT = f"""SELECT t.*, d.codigo, d.nombre AS titulo, {AUTOR} FROM entregables t
    JOIN entregables_def d ON d.id = t.def_id JOIN usuarios u ON u.id = t.autor_id"""


def entregables(pid):
    return _rows(fetch_all(_ENT + " WHERE t.proyecto_id = %s ORDER BY t.fecha DESC, t.id DESC", (pid,)))


def revisiones(pid):
    return _rows(fetch_all(f"""SELECT t.*, a.numero AS acta_numero, {AUTOR} FROM revisiones t JOIN usuarios u ON u.id = t.autor_id
        LEFT JOIN actas a ON a.id = t.acta_id WHERE t.proyecto_id = %s ORDER BY t.fecha DESC, t.id DESC""", (pid,)))


def comentarios(pid):
    return _list("comentarios", pid, "t.fecha DESC, t.id DESC")


def historial(pid):
    return _list("historial", pid, "t.fecha DESC, t.id DESC")


def insert_acta(pid, curso, fecha, autor, temas, compromisos):
    n = fetch_one("SELECT COALESCE(MAX(numero), 0) + 1 AS n FROM actas WHERE proyecto_id = %s", (pid,))["n"]
    execute("INSERT INTO actas (proyecto_id, numero, curso, fecha, autor_id, temas, compromisos) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (pid, n, curso, fecha, autor, temas, compromisos))
    return n


def entregable(eid):
    return _row(fetch_one(_ENT + " WHERE t.id = %s", (eid,)))


def acta(aid):
    return fetch_one("SELECT * FROM actas WHERE id = %s", (aid,))


def next_entregable_version(pid, did):
    return fetch_one("SELECT COALESCE(MAX(version), 0) + 1 AS n FROM entregables WHERE proyecto_id = %s AND def_id = %s", (pid, did))["n"]


def insert_entregable(pid, did, curso, version, archivo, descripcion, autor):
    return execute("""INSERT INTO entregables (proyecto_id, def_id, curso, version, archivo, descripcion, autor_id)
                      VALUES (%s,%s,%s,%s,%s,%s,%s)""", (pid, did, curso, version, archivo, descripcion, autor))


def update_entregable_estado(eid, estado, nota=None, set_nota=False):
    if set_nota:
        execute("UPDATE entregables SET estado = %s, nota = %s WHERE id = %s", (estado, nota, eid))
    else:
        execute("UPDATE entregables SET estado = %s WHERE id = %s", (estado, eid))


def insert_revision(eid, pid, acta_id, tipo, estado, nota, obs, corr, autor):
    return execute("""INSERT INTO revisiones (entregable_id, proyecto_id, acta_id, tipo, estado, nota, observaciones, correcciones, autor_id)
                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (eid, pid, acta_id, tipo, estado, nota, obs, corr, autor))


def set_revision_pdf(rid, path):
    execute("UPDATE revisiones SET pdf = %s WHERE id = %s", (path, rid))


def revision(rid):
    return _row(fetch_one("SELECT * FROM revisiones WHERE id = %s", (rid,)))


def insert_comentario(pid, sobre, sobre_id, curso, autor, texto):
    return execute("INSERT INTO comentarios (proyecto_id, sobre, sobre_id, curso, autor_id, texto) VALUES (%s,%s,%s,%s,%s,%s)",
                   (pid, sobre, sobre_id, curso, autor, texto))


def recent_comments(pids, limit=8):
    if not pids:
        return []
    marks = ",".join(["%s"] * len(pids))
    return _rows(fetch_all(f"""SELECT t.*, p.titulo AS proyecto, {AUTOR} FROM comentarios t
        JOIN usuarios u ON u.id = t.autor_id JOIN proyectos p ON p.id = t.proyecto_id
        WHERE t.proyecto_id IN ({marks}) ORDER BY t.fecha DESC, t.id DESC LIMIT {int(limit)}""", tuple(pids)))


def insert_historial(pid, curso, autor, tipo, detalle):
    execute("INSERT INTO historial (proyecto_id, curso, autor_id, tipo, detalle) VALUES (%s,%s,%s,%s,%s)", (pid, curso, autor, tipo, detalle))
