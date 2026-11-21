"""Proyectos · validación de entrada."""
from types import SimpleNamespace
from app.core.validation import texto


def proyecto(d):
    return SimpleNamespace(titulo=texto(d, "titulo", 0, 255).strip(), grupo=texto(d, "grupo", 0, 10).strip())


def cancelacion(d):
    return SimpleNamespace(motivo=texto(d, "motivo", 5, 300).strip())
