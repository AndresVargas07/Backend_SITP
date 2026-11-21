"""Capa de rutas: API REST con Flask (Blueprint) y permisos por rol en cada endpoint."""
from flask import Blueprint, g, jsonify, request, send_file
from app import schemas as v
from app.api.deps import auth
from app.repositories import repo
from app.services import project_service as svc

bp = Blueprint("api", __name__, url_prefix="/api")
EST, TEC, MET, ADM = "estudiante", "asesor_tecnico", "asesor_metodologico", "administrador"


def body():
    return request.get_json(silent=True) or {}


@bp.post("/auth/login")
def login():
    d = v.login(body())
    return jsonify(svc.login(d.email, d.password))


@bp.get("/auth/me")
@auth()
def me():
    return jsonify({"user": svc.public_user(g.user)})


@bp.post("/auth/logout")
@auth()
def logout():
    repo.delete_session(g.user["token"])
    return jsonify({"ok": True})


@bp.post("/auth/switch-rol")
@auth()
def switch_rol():
    """Cambia el rol activo de la sesión (Role Switcher)."""
    d = v.switch_rol(body())
    return jsonify(svc.switch_rol(g.user, d.rol))


@bp.get("/panel")
@auth()
def panel():
    return jsonify(svc.panel(g.user))


@bp.get("/proyectos/<int:pid>")
@auth()
def proyecto(pid):
    return jsonify(svc.detail(g.user, pid))


@bp.post("/proyectos/<int:pid>/avanzar")
@auth(MET)
def avanzar(pid):
    return jsonify(svc.avanzar_curso(g.user, pid))


@bp.post("/proyectos/<int:pid>/objetivos")
@auth(EST, MET)
def objetivo(pid):
    return jsonify(svc.add_objetivo_version(g.user, pid, v.objetivo(body()))), 201


@bp.post("/proyectos/<int:pid>/actas")
@auth(TEC, MET)
def acta(pid):
    return jsonify(svc.add_acta(g.user, pid, v.acta(body()))), 201


@bp.post("/proyectos/<int:pid>/entregables")
@auth(EST)
def entregable(pid):
    f = request.form
    def_id = int(f["defId"]) if f.get("defId", "").isdigit() else None
    return jsonify(svc.add_entregable(g.user, pid, def_id, request.files.get("archivo"), f.get("descripcion", "")[:1000])), 201


@bp.get("/entregables/<int:eid>/archivo")
@auth()
def archivo(eid):
    return send_file(svc.archivo_entregable(g.user, eid), mimetype="application/pdf")


@bp.post("/entregables/<int:eid>/revisiones")
@auth(TEC, MET)
def revisar(eid):
    return jsonify(svc.revisar(g.user, eid, v.revision(body()))), 201


@bp.get("/revisiones/<int:rid>/pdf")
@auth()
def revision_pdf(rid):
    return send_file(svc.archivo_revision(g.user, rid), mimetype="application/pdf")


@bp.patch("/proyectos/<int:pid>")
@auth(EST, MET)
def editar(pid):
    return jsonify(svc.editar_proyecto(g.user, pid, v.proyecto(body())))


@bp.post("/proyectos/<int:pid>/cancelar")
@auth(MET)
def cancelar(pid):
    return jsonify(svc.cancelar(g.user, pid, v.cancelacion(body()).motivo))


@bp.post("/proyectos/<int:pid>/comentarios")
@auth()
def comentario(pid):
    return jsonify(svc.add_comentario(g.user, pid, v.comentario(body()))), 201


# ---------- Admin: Usuarios ----------
@bp.get("/admin/usuarios")
@auth(ADM)
def admin_usuarios():
    return jsonify(svc.admin_list_users())


@bp.post("/admin/usuarios")
@auth(ADM)
def admin_crear_usuario():
    return jsonify(svc.admin_create_user(v.crear_usuario(body()))), 201


@bp.patch("/admin/usuarios/<int:uid>")
@auth(ADM)
def admin_editar_usuario(uid):
    return jsonify(svc.admin_update_user(uid, v.editar_usuario(body()), g.user["id"]))


@bp.delete("/admin/usuarios/<int:uid>")
@auth(ADM)
def admin_eliminar_usuario(uid):
    return jsonify(svc.admin_delete_user(uid, g.user["id"]))

