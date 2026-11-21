"""Entregables · validación de entrada."""
from types import SimpleNamespace
from app.core.validation import opcion, opcional, texto


def subida(form):
    d = form.get("defId", "")
    return SimpleNamespace(defId=int(d) if d.isdigit() else None, descripcion=form.get("descripcion", "")[:1000])


def revision(d):
    return SimpleNamespace(actaId=opcional(d, "actaId", int), observaciones=texto(d, "observaciones", 0, 4000),
                           correcciones=texto(d, "correcciones", 0, 4000), nota=opcional(d, "nota", float, 0, 5),
                           estado=opcion(d, "estado", (None, "", "Revisado", "Para corrección", "Aprobado"), None) or None)
