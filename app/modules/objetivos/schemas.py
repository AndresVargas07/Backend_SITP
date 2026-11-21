"""Objetivos · validación de entrada."""
from types import SimpleNamespace
from app.core.validation import opcion, opcional, texto


def objetivo(d):
    return SimpleNamespace(objetivoId=opcional(d, "objetivoId", int), tipo=opcion(d, "tipo", ("General", "Específico"), "Específico"),
                           texto=texto(d, "texto", 10, 1000), motivo=texto(d, "motivo", 0, 300))
