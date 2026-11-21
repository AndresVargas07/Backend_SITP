"""Seguimiento · capa de negocio: comentarios."""
from app.core.http import EST, MET, TEC
from app.modules.proyectos.service import accesible
from app.modules.seguimiento import repository as repo


def add_comentario(user, pid, data):
    p = accesible(user, pid, EST, TEC, MET)  # hilo compartido entre estudiantes y asesores
    cid = repo.insert_comentario(pid, data.sobre, data.sobreId if data.sobre != "proyecto" else None,
                                 p["cursoActual"], user["id"], data.texto.strip())
    return {"id": cid}
