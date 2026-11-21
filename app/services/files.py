"""Almacenamiento de PDF: guarda las entregas con nombre normalizado y genera el PDF de observaciones técnicas."""
import os
import re
import unicodedata
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from app.config import settings
from app.errors import ApiError

TEAL = colors.HexColor("#00a3bf")


def _slug(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")


def _abs(rel):
    return os.path.join(settings.UPLOAD_DIR, rel)


def full_path(rel):
    path = _abs(rel)
    if not rel or not os.path.isfile(path):
        raise ApiError(404, "El archivo ya no está disponible")
    return path


def save_entrega(file, p, d, version):
    """Valida que sea PDF y lo guarda como G04_M1_E1_Planteamiento_del_problema_v2.pdf"""
    if not file or not file.filename:
        raise ApiError(422, "Selecciona el archivo PDF del entregable")
    data = file.read()
    if not data.startswith(b"%PDF") or not file.filename.lower().endswith(".pdf"):
        raise ApiError(422, "El archivo debe ser un PDF")
    if len(data) > settings.MAX_PDF_MB * 1024 * 1024:
        raise ApiError(413, f"El PDF supera {settings.MAX_PDF_MB} MB")
    rel = f"p{p['id']}/G{p['grupo']}_M{d['curso']}_{d['codigo']}_{_slug(d['nombre'])}_v{version}.pdf"
    os.makedirs(os.path.dirname(_abs(rel)), exist_ok=True)
    with open(_abs(rel), "wb") as f:
        f.write(data)
    return rel


def observaciones_pdf(rid, p, materia, e, acta, autor, obs, corr, fecha):
    """PDF con las observaciones y correcciones del asesor técnico, vinculado al acta y al entregable."""
    rel = f"p{p['id']}/observaciones/G{p['grupo']}_M{e['curso']}_{e['codigo']}_v{e['version']}_Observaciones_tecnicas_R{rid}.pdf"
    os.makedirs(os.path.dirname(_abs(rel)), exist_ok=True)
    st = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=st["Heading2"], textColor=colors.HexColor("#00768a"))
    body = ParagraphStyle("b", parent=st["BodyText"], leading=15)
    txt = lambda t: Paragraph(escape(t).replace("\n", "<br/>"), body)
    info = [["Proyecto", txt(p["titulo"])], ["Materia", materia], ["Grupo", p["grupo"]],
            ["Entregable", txt(f"{e['codigo']} · {e['titulo']} (versión {e['version']})")], ["Archivo revisado", txt(os.path.basename(e["archivo"]))],
            ["Acta", f"N.º {acta['numero']:02d} del {acta['fecha']}" if acta else "Sin acta vinculada"],
            ["Asesor técnico", autor["nombre"]], ["Fecha", fecha]]
    t = Table(info, colWidths=[38 * mm, 132 * mm])
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#0a3f4a")),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dbe8eb")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    flow = [Paragraph("Universidad Cooperativa de Colombia · SITP", ParagraphStyle("t", parent=st["Normal"], textColor=TEAL)),
            Paragraph("Observaciones del asesor técnico", st["Title"]), t, Spacer(1, 10)]
    if obs:
        flow += [Paragraph("Observaciones y sugerencias", h), txt(obs)]
    if corr:
        flow += [Paragraph("Correcciones que debe realizar el estudiante", h), txt(corr)]
    SimpleDocTemplate(_abs(rel), pagesize=A4, title=f"Observaciones técnicas {e['codigo']} v{e['version']}", author=autor["nombre"],
                      leftMargin=20 * mm, rightMargin=20 * mm).build(flow)
    return rel
