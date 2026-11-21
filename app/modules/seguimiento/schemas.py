"""Seguimiento · validación de entrada."""
from types import SimpleNamespace
from app.core.validation import opcion, opcional, texto


def comentario(d):
    return SimpleNamespace(sobre=opcion(d, "sobre", ("proyecto", "entregable", "acta"), "proyecto"),
                           sobreId=opcional(d, "sobreId", int), texto=texto(d, "texto", 1, 2000))
