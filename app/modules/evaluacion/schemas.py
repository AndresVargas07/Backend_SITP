"""Evaluación · validación de entrada."""
from types import SimpleNamespace
from app.core.errors import ApiError
from app.core.validation import opcion, texto

CONCEPTOS = ("Aprobado", "Observado / Plan de mejora")


def evaluacion(d, criterios):
    pts = d.get("puntajes") if isinstance(d.get("puntajes"), dict) else {}
    puntajes = {}
    for c in criterios:
        v = pts.get(str(c["id"]))
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 5:
            raise ApiError(422, f"Califica «{c['nombre']}» entre 0 y 5")
        puntajes[str(c["id"])] = round(float(v), 1)
    concepto = opcion(d, "concepto", CONCEPTOS, None)
    obs = texto(d, "observaciones", 0, 3000).strip()
    if concepto != "Aprobado" and len(obs) < 10:
        raise ApiError(422, "Un concepto «Observado» requiere observaciones o plan de mejora (mín. 10 caracteres)")
    return SimpleNamespace(puntajes=puntajes, concepto=concepto, observaciones=obs)
