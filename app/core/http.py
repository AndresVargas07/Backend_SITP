"""Utilidades HTTP comunes: roles y lectura del cuerpo JSON."""
from flask import request

# Roles globales (cuenta) y roles contextuales (según el proyecto asignado al docente)
EST, DOC, ADM = "estudiante", "docente", "administrador"
TEC, MET, JUR = "asesor_tecnico", "asesor_metodologico", "jurado"


def body():
    return request.get_json(silent=True) or {}


def rol_en(p, user):
    """Rol del usuario dentro de un proyecto.
    El administrador en modo Swap opera libremente bajo el rol activo."""
    if user.get("rol_global") == ADM or user.get("rol") == ADM:
        return user.get("rol_efectivo") or ADM

    rol_activo = user.get("rol_efectivo") or user.get("rol")
    if rol_activo in (TEC, MET, JUR):
        col_map = {TEC: "asesorTecnicoId", MET: "asesorMetodologicoId", JUR: "juradoId"}
        if p.get(col_map.get(rol_activo)) == user["id"]:
            return rol_activo
    if rol_activo == EST:
        if user["id"] in (p.get("estudiantes") or []):
            return EST

    if user["rol"] == DOC:
        return next((r for col, r in (("asesorTecnicoId", TEC), ("asesorMetodologicoId", MET), ("juradoId", JUR)) if p.get(col) == user["id"]), None)
    return user["rol"]
