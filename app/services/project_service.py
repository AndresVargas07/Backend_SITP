"""Capa de servicios: reglas de negocio del SITP (trazabilidad entre cursos, versiones y evaluación)."""
import secrets
from datetime import date, datetime
from app.errors import ApiError
from app.repositories import repo
from app.security import verify_password, hash_password
from app.services import files



def cursos():
    """Materias (los tres cursos) leídas de la base de datos."""
    return repo.materias()


def public_user(u):
    return {k: u.get(k) for k in ("id", "nombre", "email", "rol", "programa", "roles")}


# ---------- Autenticación ----------
def login(email, password):
    u = repo.user_by_email(email.strip())
    if not u or not verify_password(password, u["password_hash"]):
        raise ApiError(401, "Correo o contraseña incorrectos")
    roles = repo._user_roles(u["id"])
    # Rol activo inicial: primer rol de la tabla (o el legacy)
    rol_activo = roles[0] if roles else u["rol"]
    token = secrets.token_hex(32)
    repo.create_session(token, u["id"], rol_activo)
    pub = public_user(u)
    pub["roles"] = roles
    pub["rolActivo"] = rol_activo
    return {"token": token, "user": pub}


def switch_rol(user, nuevo_rol):
    """Cambia el rol activo de la sesión actual."""
    roles = user.get("roles") or []
    # Administrador puede cambiar a cualquier rol del sistema; otros solo a sus roles asignados
    if user["rol"] != "administrador" and nuevo_rol not in roles:
        raise ApiError(403, "No tienes ese rol asignado")
    repo.set_session_rol(user["token"], nuevo_rol)
    return {"rolActivo": nuevo_rol}


# ---------- Admin: CRUD de usuarios ----------
def admin_list_users():
    return repo.admin_all_users()


def admin_create_user(data):
    if repo.user_by_email(data.email):
        raise ApiError(409, "Ya existe un usuario con ese correo")
    ph = hash_password(data.password)
    uid = repo.admin_create_user(data.nombre, data.email, ph, data.roles, data.programa)
    return {"id": uid}


def admin_update_user(uid, data, current_user_id):
    u = repo.admin_user_by_id(uid)
    if not u:
        raise ApiError(404, "Usuario no encontrado")
    ph = hash_password(data.password) if data.password else None
    repo.admin_update_user(uid, nombre=data.nombre, email=data.email, roles=data.roles,
                           programa=data.programa, activo=data.activo, password_hash=ph)
    return {"ok": True}


def admin_delete_user(uid, current_user_id):
    if uid == current_user_id:
        raise ApiError(400, "No puedes eliminar tu propia cuenta")
    u = repo.admin_user_by_id(uid)
    if not u:
        raise ApiError(404, "Usuario no encontrado")
    repo.admin_delete_user(uid)
    return {"ok": True}


# ---------- Consultas ----------
def _accessible(user, pid):
    p = repo.project_for(user, pid)
    if p:
        return p
    raise ApiError(403 if repo.project_exists(pid) else 404,
                        "No estás vinculado a este proyecto" if repo.project_exists(pid) else "Proyecto no encontrado")


def _with_curso(p, cs):
    p["curso"] = cs[p["cursoActual"]]
    return p


def panel(user):
    cs = cursos()
    ps = [_with_curso(p, cs) for p in repo.projects_for(user)]
    return {"cursos": cs, "proyectos": ps, "comentarios": repo.recent_comments([p["id"] for p in ps])}


def detail(user, pid):
    cs = cursos()
    p = _with_curso(_accessible(user, pid), cs)
    return {**p, "cursos": cs, "catalogo": repo.entregables_def(), "objetivos": repo.objetivos(pid), "actas": repo.actas(pid),
            "entregables": repo.entregables(pid), "revisiones": repo.revisiones(pid), "comentarios": repo.comentarios(pid), "historial": repo.historial(pid)}


# ---------- Comandos ----------
def _log(p, user, tipo, detalle):
    repo.insert_historial(p["id"], p["cursoActual"], user["id"], tipo, detalle)


def add_objetivo_version(user, pid, data):
    p = _accessible(user, pid)
    oid = data.objetivoId
    if oid:
        o = repo.objetivo(oid)
        if not o or o["proyecto_id"] != pid:
            raise ApiError(400, "Objetivo inválido")
        tipo = o["tipo"]
    else:
        tipo = data.tipo
        oid = repo.insert_objetivo(pid, tipo)
    motivo = data.motivo.strip() or "Sin motivo indicado"
    v = repo.insert_objetivo_version(oid, data.texto.strip(), motivo, p["cursoActual"], user["id"])
    _log(p, user, "Objetivo", f"Objetivo {tipo.lower()} versión {v}: {motivo}")
    return {"id": oid, "version": v}


def add_acta(user, pid, data):
    p = _accessible(user, pid)
    n = repo.insert_acta(pid, p["cursoActual"], data.fecha or date.today(), user["id"], data.temas.strip(), data.compromisos.strip())
    _log(p, user, "Acta", f"Acta N.º {n:02d} registrada")
    return {"numero": n}


def _abierto(p):
    if p["estado"] != "En curso":
        raise ApiError(400, f"El proyecto está {p['estado'].lower()}; no admite cambios")


def add_entregable(user, pid, def_id, file, descripcion):
    """El estudiante sube el PDF de un entregable de la materia actual; cada carga es una nueva versión."""
    p = _accessible(user, pid)
    _abierto(p)
    d = repo.entregable_def(def_id) if def_id else None
    if not d or d["curso"] != p["cursoActual"]:
        raise ApiError(422, "Selecciona un entregable de la materia actual")
    v = repo.next_entregable_version(pid, d["id"])
    rel = files.save_entrega(file, p, d, v)
    eid = repo.insert_entregable(pid, d["id"], d["curso"], v, rel, descripcion.strip(), user["id"])
    _log(p, user, "Entregable", f"{d['codigo']} · {d['nombre']} (v{v}) subido como {rel.split('/')[-1]}")
    return {"id": eid, "version": v, "archivo": rel.split("/")[-1]}


def archivo_entregable(user, eid):
    e = repo.entregable(eid)
    if not e:
        raise ApiError(404, "Entregable no encontrado")
    _accessible(user, e["proyectoId"])
    return files.full_path(e["archivo"])


def archivo_revision(user, rid):
    r = repo.revision(rid)
    if not r or not r["pdf"]:
        raise ApiError(404, "Esta revisión no tiene PDF de observaciones")
    _accessible(user, r["proyectoId"])
    return files.full_path(r["pdf"])


def revisar(user, eid, data):
    """Revisión de un asesor. El técnico no califica: comenta y, si hay observaciones, se genera un PDF.
    El metodológico asigna estado y nota. Ambas quedan vinculadas al acta elegida."""
    e = repo.entregable(eid)
    if not e:
        raise ApiError(404, "Entregable no encontrado")
    p = _accessible(user, e["proyectoId"])
    _abierto(p)
    acta = repo.acta(data.actaId) if data.actaId else None
    if data.actaId and (not acta or acta["proyecto_id"] != p["id"]):
        raise ApiError(422, "El acta no pertenece a este proyecto")
    obs, corr = data.observaciones.strip(), data.correcciones.strip()
    tecnica = user["rol"] == "asesor_tecnico"
    if tecnica:
        estado, nota = ("Para corrección" if corr else "Revisado"), None
    else:
        estado, nota = data.estado, data.nota
        if not estado:
            raise ApiError(422, "Selecciona el estado del entregable")
    rid = repo.insert_revision(eid, p["id"], acta["id"] if acta else None, "tecnica" if tecnica else "metodologica", estado, nota, obs, corr, user["id"])
    if tecnica and (obs or corr):
        repo.set_revision_pdf(rid, files.observaciones_pdf(rid, p, cursos()[e["curso"]], e, acta, user, obs, corr, datetime.now().strftime("%Y-%m-%d %H:%M")))
    if not (tecnica and e["estado"] == "Aprobado"):  # el técnico no reabre un entregable ya aprobado
        repo.update_entregable_estado(eid, estado, nota, set_nota=not tecnica)
    quien = "Revisión técnica" if tecnica else "Revisión metodológica"
    _log(p, user, "Cambio de estado", f"{quien} de {e['codigo']} · {e['titulo']} (v{e['version']}): {estado}"
         + (f" — nota {nota:.1f}" if nota is not None else "") + (f" · Acta N.º {acta['numero']:02d}" if acta else ""))
    return {"id": rid, "estado": estado}


def editar_proyecto(user, pid, data):
    p = _accessible(user, pid)
    _abierto(p)
    cambios = []
    if data.titulo and data.titulo != p["titulo"]:
        cambios.append(("Cambio de nombre", f"«{p['titulo']}» → «{data.titulo}»"))
    if data.grupo and data.grupo != p["grupo"]:
        cambios.append(("Modificación", f"Grupo {p['grupo']} → {data.grupo}"))
    if not cambios:
        raise ApiError(422, "No hay cambios para guardar")
    repo.update_project(pid, titulo=data.titulo or None, grupo=data.grupo or None)
    for tipo, detalle in cambios:
        _log(p, user, tipo, detalle)
    return {"ok": True}


def cancelar(user, pid, motivo):
    p = _accessible(user, pid)
    _abierto(p)
    repo.update_project(pid, estado="Cancelado")
    _log(p, user, "Cancelación", f"Proyecto cancelado. Motivo: {motivo}")
    return {"ok": True}


def add_comentario(user, pid, data):
    p = _accessible(user, pid)
    cid = repo.insert_comentario(pid, data.sobre, data.sobreId if data.sobre != "proyecto" else None, p["cursoActual"], user["id"], data.texto.strip())
    return {"id": cid}


def avanzar_curso(user, pid):
    p = _accessible(user, pid)
    _abierto(p)
    cs = cursos()
    if p["cursoActual"] >= 3:
        repo.update_project(pid, estado="Finalizado")
        _log(p, user, "Cierre", "Proyecto finalizado al terminar Aplicación Práctica del Trabajo de Grado")
    else:
        nuevo = p["cursoActual"] + 1
        repo.update_project(pid, curso=nuevo)
        _log({**p, "cursoActual": nuevo}, user, "Cambio de curso", f"El proyecto avanzó a {cs[nuevo]} conservando su historial completo.")
    return {"ok": True}
