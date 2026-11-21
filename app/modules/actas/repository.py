"""Actas · capa de datos: actas, compromisos y firma."""
from app.core.database import execute, fetch_all, fetch_one
from app.core.serializers import AUTOR, rows


def actas(pid):
    rs = rows(fetch_all(f"""SELECT t.*, {AUTOR}, f.nombre AS firmante FROM actas t JOIN usuarios u ON u.id = t.autor_id
        LEFT JOIN usuarios f ON f.id = t.firmada_por WHERE t.proyecto_id = %s ORDER BY t.numero DESC""", (pid,)))
    ks = rows(fetch_all("""SELECT k.* FROM compromisos k JOIN actas a ON a.id = k.acta_id
        WHERE a.proyecto_id = %s ORDER BY k.fecha_limite, k.id""", (pid,)))
    for a in rs:
        a["compromisos"] = [k for k in ks if k["actaId"] == a["id"]]
    return rs


def acta(aid):
    return fetch_one("SELECT * FROM actas WHERE id = %s", (aid,))


def compromiso(cid):
    return fetch_one("SELECT k.*, a.proyecto_id FROM compromisos k JOIN actas a ON a.id = k.acta_id WHERE k.id = %s", (cid,))


def insert_acta(pid, curso, fecha, autor, temas, compromisos):
    n = fetch_one("SELECT COALESCE(MAX(numero), 0) + 1 AS n FROM actas WHERE proyecto_id = %s", (pid,))["n"]
    aid = execute("INSERT INTO actas (proyecto_id, numero, curso, fecha, autor_id, temas) VALUES (%s,%s,%s,%s,%s,%s)",
                  (pid, n, curso, fecha, autor, temas))
    for k in compromisos:
        execute("INSERT INTO compromisos (acta_id, descripcion, responsable, fecha_limite) VALUES (%s,%s,%s,%s)",
                (aid, k.descripcion, k.responsable, k.fecha_limite))
    return n


def firmar(aid, uid):
    execute("UPDATE actas SET firmada = 1, firmada_por = %s, firmada_en = NOW() WHERE id = %s", (uid, aid))


def set_cumplido(cid, valor):
    execute("UPDATE compromisos SET cumplido = %s WHERE id = %s", (1 if valor else 0, cid))
