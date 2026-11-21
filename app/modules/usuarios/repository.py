"""Usuarios · capa de datos para la administración de cuentas y asignaciones."""
from app.core.database import execute, fetch_all, fetch_one
from app.core.serializers import row, rows


def user_roles(uid):
    rs = fetch_all("SELECT rol FROM usuario_roles WHERE usuario_id = %s", (uid,))
    return [r["rol"] for r in rs] if rs else []


def usuarios():
    rs = fetch_all("""SELECT u.id, u.nombre, u.email, u.rol, u.programa, u.activo,
        (SELECT COUNT(*) FROM proyectos p WHERE u.id IN (p.asesor_tecnico_id, p.asesor_metodologico_id, p.jurado_id)
           OR p.id IN (SELECT proyecto_id FROM proyecto_estudiantes WHERE estudiante_id = u.id)) AS proyectos
        FROM usuarios u ORDER BY u.nombre""")
    out = []
    for r in rs:
        d = row(r)
        d["roles"] = user_roles(d["id"])
        if not d["roles"] and d.get("rol"):
            d["roles"] = [d["rol"]]
        out.append(d)
    return out


def usuario(uid):
    r = fetch_one("SELECT * FROM usuarios WHERE id = %s", (uid,))
    if not r:
        return None
    d = dict(r)
    d["roles"] = user_roles(uid)
    return d


def email_existe(email, exclude_id=None):
    if exclude_id:
        return fetch_one("SELECT id FROM usuarios WHERE LOWER(email) = LOWER(%s) AND id != %s", (email, exclude_id))
    return fetch_one("SELECT id FROM usuarios WHERE LOWER(email) = LOWER(%s)", (email,))


def _legacy_rol(roles):
    if not roles:
        return "estudiante"
    for r in roles:
        if r in ("estudiante", "docente", "administrador"):
            return r
        if r in ("asesor_tecnico", "asesor_metodologico", "jurado"):
            return "docente"
    return roles[0]


def crear(nombre, email, roles, programa, pw_hash):
    rol_primary = _legacy_rol(roles)
    uid = execute("INSERT INTO usuarios (nombre, email, rol, programa, password_hash) VALUES (%s,%s,%s,%s,%s)",
                  (nombre, email, rol_primary, programa, pw_hash))
    for r in roles:
        execute("INSERT IGNORE INTO usuario_roles (usuario_id, rol) VALUES (%s, %s)", (uid, r))
    return uid


def actualizar(uid, nombre=None, email=None, roles=None, programa=None, activo=None, pw_hash=None):
    sets, params = [], []
    if nombre is not None:
        sets.append("nombre = %s"); params.append(nombre)
    if email is not None:
        sets.append("email = %s"); params.append(email)
    if programa is not None:
        sets.append("programa = %s"); params.append(programa)
    if activo is not None:
        sets.append("activo = %s"); params.append(1 if activo else 0)
    if pw_hash is not None:
        sets.append("password_hash = %s"); params.append(pw_hash)
    if roles is not None and roles:
        sets.append("rol = %s"); params.append(_legacy_rol(roles))

    if sets:
        params.append(uid)
        execute(f"UPDATE usuarios SET {', '.join(sets)} WHERE id = %s", tuple(params))

    if roles is not None:
        execute("DELETE FROM usuario_roles WHERE usuario_id = %s", (uid,))
        for r in roles:
            execute("INSERT IGNORE INTO usuario_roles (usuario_id, rol) VALUES (%s, %s)", (uid, r))

    if activo is False:
        execute("DELETE FROM sesiones WHERE usuario_id = %s", (uid,))


def eliminar(uid):
    execute("DELETE FROM usuarios WHERE id = %s", (uid,))


def docentes_activos(ids):
    marks = ",".join(["%s"] * len(ids))
    return fetch_all(f"""SELECT DISTINCT u.id FROM usuarios u
        LEFT JOIN usuario_roles ur ON ur.usuario_id = u.id
        WHERE u.activo = 1 AND (u.rol = 'docente' OR ur.rol IN ('docente','asesor_tecnico','asesor_metodologico','jurado'))
        AND u.id IN ({marks})""", tuple(ids))


def asignado(uid):
    """True si el usuario está vinculado a algún proyecto."""
    return bool(fetch_one("""SELECT 1 AS x FROM proyectos p WHERE %(u)s IN (p.asesor_tecnico_id, p.asesor_metodologico_id, p.jurado_id)
        OR p.id IN (SELECT proyecto_id FROM proyecto_estudiantes WHERE estudiante_id = %(u)s) LIMIT 1""", {"u": uid}))
