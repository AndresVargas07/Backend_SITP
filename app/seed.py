"""Datos ficticios para el entorno de prueba (no son datos institucionales reales)."""
from app.security import hash_password

MATERIAS = {1: "Ideación, Emprendimiento y Desarrollo Tecnológico", 2: "Construcción del Trabajo de Grado", 3: "Aplicación Práctica del Trabajo de Grado"}
CURSO1 = MATERIAS[1]
# Catálogo de entregables por materia (se puede editar en la tabla entregables_def)
ENTREGABLES = [
    (1, "E1", "Planteamiento del problema"), (1, "E2", "Estado del arte y objetivos"), (1, "E8", "Documento final del anteproyecto"),
    (2, "E1", "Diseño metodológico y arquitectura"), (2, "E2", "Avance del trabajo de grado"),
    (3, "E1", "Resultados de la aplicación práctica"), (3, "E2", "Informe final"),
]


def seed(cur):
    pw = hash_password("Ucc2026*")
    cur.executemany("INSERT INTO usuarios (id, nombre, email, rol, programa, password_hash) VALUES (%s,%s,%s,%s,%s,%s)", [
        (1, "Laura Restrepo Gil", "laura.restrepo@campusucc.edu.co", "estudiante", "Ingeniería de Software", pw),
        (2, "Samuel Ortiz Mejía", "samuel.ortiz@campusucc.edu.co", "estudiante", "Ingeniería de Software", pw),
        (3, "Valentina Ríos Cano", "valentina.rios@campusucc.edu.co", "estudiante", "Ingeniería Civil", pw),
        (4, "Mateo Zapata Henao", "mateo.zapata@campusucc.edu.co", "estudiante", "Ingeniería de Software", pw),
        (5, "Ing. Carolina Mesa", "carolina.mesa@ucc.edu.co", "asesor_tecnico", None, pw),
        (6, "Mg. Julián Arango", "julian.arango@ucc.edu.co", "asesor_metodologico", None, pw),
    ])
    cur.executemany("INSERT INTO materias (id, nombre) VALUES (%s,%s)", list(MATERIAS.items()))
    cur.executemany("INSERT INTO entregables_def (materia_id, codigo, nombre) VALUES (%s,%s,%s)", ENTREGABLES)
    cur.executemany("INSERT INTO proyectos (id, titulo, programa, grupo, curso_actual, estado, asesor_tecnico_id, asesor_metodologico_id, creado) VALUES (%s,%s,%s,%s,%s,%s,5,6,%s)", [
        (1, "App móvil para la gestión de residuos en conjuntos residenciales", "Ingeniería de Software", "04", 2, "En curso", "2026-02-10 12:00:00"),
        (2, "Evaluación de mezclas de concreto con agregado reciclado", "Ingeniería Civil", "02", 1, "En curso", "2026-08-04 12:00:00"),
        (3, "Plataforma web de tutorías entre pares para primer semestre", "Ingeniería de Software", "01", 3, "Finalizado", "2025-08-01 12:00:00"),
    ])
    cur.executemany("INSERT INTO proyecto_estudiantes VALUES (%s,%s)", [(1, 1), (1, 2), (2, 3), (3, 4)])
    cur.executemany("INSERT INTO objetivos (id, proyecto_id, tipo) VALUES (%s,%s,%s)", [(1, 1, "General"), (2, 1, "Específico"), (3, 2, "General"), (4, 3, "General")])
    cur.executemany("INSERT INTO objetivo_versiones (objetivo_id, version, texto, motivo, curso, autor_id, fecha) VALUES (%s,%s,%s,%s,%s,%s,%s)", [
        (1, 1, "Desarrollar una aplicación móvil para registrar la separación de residuos.", "Versión inicial", 1, 1, "2026-02-20 12:00:00"),
        (1, 2, "Desarrollar y evaluar una aplicación móvil que permita registrar y consultar la separación de residuos en conjuntos residenciales de Medellín.", "Ajuste de alcance acordado en el Acta N.º 02", 2, 1, "2026-08-15 12:00:00"),
        (2, 1, "Caracterizar el proceso actual de recolección en tres conjuntos residenciales.", "Versión inicial", 1, 2, "2026-02-20 12:00:00"),
        (3, 1, "Evaluar la resistencia a compresión de concretos con 20 % y 40 % de agregado reciclado.", "Versión inicial", 1, 3, "2026-08-20 12:00:00"),
        (4, 1, "Desarrollar y evaluar una plataforma web de tutorías entre pares.", "Versión inicial", 1, 4, "2025-08-15 12:00:00"),
    ])
    cur.executemany("INSERT INTO actas (proyecto_id, numero, curso, fecha, autor_id, temas, compromisos) VALUES (%s,%s,%s,%s,%s,%s,%s)", [
        (1, 1, 1, "2026-03-05", 5, "Revisión del planteamiento del problema.", "Ajustar la pregunta de investigación."),
        (1, 2, 2, "2026-08-12", 5, "Arquitectura preliminar del prototipo.", "Entregar modelo de datos."),
        (2, 1, 1, "2026-09-02", 6, "Revisión del cronograma.", "Definir ensayos de laboratorio."),
    ])
    cur.executemany("INSERT INTO comentarios (proyecto_id, sobre, sobre_id, curso, autor_id, texto, fecha) VALUES (%s,%s,%s,%s,%s,%s,%s)", [
        (1, "proyecto", None, 2, 6, "Falta justificar la elección de la base de datos frente a los requerimientos.", "2026-09-03 12:00:00"),
        (1, "proyecto", None, 2, 5, "De acuerdo. Sugiero incluir el diagrama de despliegue del entorno de prueba.", "2026-09-04 12:00:00"),
        (2, "proyecto", None, 1, 5, "Delimitar el tipo de agregado reciclado y su procedencia.", "2026-09-12 12:00:00"),
    ])
    cur.executemany("INSERT INTO historial (proyecto_id, fecha, curso, autor_id, tipo, detalle) VALUES (%s,%s,%s,6,%s,%s)", [
        (1, "2026-02-10 12:00:00", 1, "Proyecto", f"Proyecto registrado en {CURSO1}."),
        (1, "2026-06-10 12:00:00", 2, "Cambio de curso", "El proyecto avanzó a Construcción del Trabajo de Grado conservando su historial."),
        (2, "2026-08-04 12:00:00", 1, "Proyecto", f"Proyecto registrado en {CURSO1}."),
        (3, "2026-06-05 12:00:00", 3, "Cierre", "Proyecto finalizado al terminar Aplicación Práctica del Trabajo de Grado."),
    ])
