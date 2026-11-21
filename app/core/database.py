"""Conexión a MySQL con mysql-connector-python (pool de conexiones)."""
import os
import sys
from contextlib import contextmanager
from pathlib import Path

# Evitar que app/core sombree la biblioteca estándar http de Python si se ejecuta este archivo directamente
_cur_dir = os.path.normcase(os.path.abspath(str(Path(__file__).resolve().parent)))
sys.path = [p for p in sys.path if os.path.normcase(os.path.abspath(p)) != _cur_dir]
_base_dir = str(Path(__file__).resolve().parent.parent.parent)
if _base_dir not in sys.path:
    sys.path.insert(0, _base_dir)

import mysql.connector
from mysql.connector import pooling
# pyrefly: ignore[missing-import]
from app.core.config import settings

_pool = None


def _server_conn():
    return mysql.connector.connect(host=settings.DB_HOST, port=settings.DB_PORT, user=settings.DB_USER, password=settings.DB_PASSWORD)


def init_db():
    """Crea la base, las tablas y los datos de prueba si aún no existen."""
    global _pool
    conn = _server_conn()
    conn.cursor().execute(f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.close()
    _pool = pooling.MySQLConnectionPool(pool_name="sitp", pool_size=5, host=settings.DB_HOST, port=settings.DB_PORT,
                                        user=settings.DB_USER, password=settings.DB_PASSWORD, database=settings.DB_NAME,
                                        charset="utf8mb4", collation="utf8mb4_unicode_ci", autocommit=False)
    with transaction() as cur:  # base de una versión anterior (sin evaluaciones): se recrea la base de prueba
        cur.execute("SELECT table_name AS t FROM information_schema.tables WHERE table_schema = %s", (settings.DB_NAME,))
        tablas = [r["t"] for r in cur.fetchall()]
        if "usuarios" in tablas and "evaluaciones" not in tablas:
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            for t in tablas:
                cur.execute(f"DROP TABLE IF EXISTS `{t}`")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    sql = (Path(__file__).resolve().parent.parent / "database" / "schema.sql").read_text(encoding="utf-8")
    lines = [l for l in sql.splitlines() if not l.strip().startswith("--")]
    sql_clean = "\n".join(lines)
    with transaction() as cur:
        for stmt in sql_clean.split(";"):
            clean = stmt.strip()
            if clean:
                cur.execute(clean)

        # Migración automática de columnas y roles si la BD ya existía
        cur.execute("SELECT COUNT(*) AS n FROM information_schema.columns WHERE table_schema = %s AND table_name = 'sesiones' AND column_name = 'rol_activo'", (settings.DB_NAME,))
        if cur.fetchone()["n"] == 0:
            cur.execute("ALTER TABLE sesiones ADD COLUMN rol_activo VARCHAR(40) NULL")

        cur.execute("SELECT COUNT(*) AS n FROM usuario_roles")
        if cur.fetchone()["n"] == 0:
            cur.execute("""INSERT IGNORE INTO usuario_roles (usuario_id, rol)
                           SELECT id, rol FROM usuarios WHERE rol IN ('estudiante','docente','administrador')""")
            cur.execute("""INSERT IGNORE INTO usuario_roles (usuario_id, rol)
                           SELECT id, 'asesor_tecnico' FROM usuarios WHERE rol = 'docente'""")
            cur.execute("""INSERT IGNORE INTO usuario_roles (usuario_id, rol)
                           SELECT id, 'asesor_metodologico' FROM usuarios WHERE rol = 'docente'""")
            cur.execute("""INSERT IGNORE INTO usuario_roles (usuario_id, rol)
                           SELECT id, 'jurado' FROM usuarios WHERE rol = 'docente'""")

        cur.execute("SELECT COUNT(*) AS n FROM usuarios")
        if cur.fetchone()["n"] == 0:
            # pyrefly: ignore[missing-import]
            from app.database.seed import seed
            seed(cur)


@contextmanager
def transaction():
    """Abre una conexión del pool; confirma al terminar o revierte si hay error."""
    conn = _pool.get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def fetch_all(sql, params=()):
    with transaction() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_one(sql, params=()):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    with transaction() as cur:
        cur.execute(sql, params)
        return cur.lastrowid


if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada correctamente.")
