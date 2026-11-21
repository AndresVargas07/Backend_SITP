"""Conexión a MySQL con mysql-connector-python (pool de conexiones)."""
from contextlib import contextmanager
from pathlib import Path
import mysql.connector
from mysql.connector import pooling
from app.config import settings

_pool = None
OLD_TABLES = ("historial", "comentarios", "entregables", "actas", "objetivo_versiones", "objetivos", "proyecto_estudiantes", "proyectos", "sesiones", "usuarios")


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
    with transaction() as cur:  # esquema anterior (sin materias): se recrea la base de prueba
        cur.execute("SELECT COUNT(*) AS n FROM information_schema.tables WHERE table_schema = %s AND table_name IN ('usuarios', 'revisiones')", (settings.DB_NAME,))
        if cur.fetchone()["n"] == 1:
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            for t in OLD_TABLES:
                cur.execute(f"DROP TABLE IF EXISTS {t}")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    sql = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    with transaction() as cur:
        for stmt in filter(str.strip, sql.split(";")):
            cur.execute(stmt)
        cur.execute("SELECT COUNT(*) AS n FROM usuarios")
        if cur.fetchone()["n"] == 0:
            from app.seed import seed
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
