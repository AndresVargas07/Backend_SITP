-- Esquema MySQL del SITP (Sistema de Trazabilidad de Proyectos de Investigación Formativa)
CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  rol ENUM('estudiante','asesor_tecnico','asesor_metodologico') NOT NULL,
  programa VARCHAR(80) NULL,
  password_hash VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sesiones (
  token CHAR(64) PRIMARY KEY,
  usuario_id INT NOT NULL,
  expira DATETIME NOT NULL,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Materias (los tres cursos del proceso) y catálogo de entregables de cada una
CREATE TABLE IF NOT EXISTS materias (
  id TINYINT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS entregables_def (
  id INT AUTO_INCREMENT PRIMARY KEY,
  materia_id TINYINT NOT NULL,
  codigo VARCHAR(5) NOT NULL,
  nombre VARCHAR(150) NOT NULL,
  UNIQUE (materia_id, codigo),
  FOREIGN KEY (materia_id) REFERENCES materias(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS proyectos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  titulo VARCHAR(255) NOT NULL,
  programa VARCHAR(80) NOT NULL,
  grupo VARCHAR(10) NOT NULL,
  curso_actual TINYINT NOT NULL DEFAULT 1,
  estado ENUM('En curso','Finalizado','Cancelado') NOT NULL DEFAULT 'En curso',
  asesor_tecnico_id INT NOT NULL,
  asesor_metodologico_id INT NOT NULL,
  creado DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (asesor_tecnico_id) REFERENCES usuarios(id),
  FOREIGN KEY (asesor_metodologico_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS proyecto_estudiantes (
  proyecto_id INT NOT NULL,
  estudiante_id INT NOT NULL,
  PRIMARY KEY (proyecto_id, estudiante_id),
  FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
  FOREIGN KEY (estudiante_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS objetivos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  proyecto_id INT NOT NULL,
  tipo ENUM('General','Específico') NOT NULL,
  FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS objetivo_versiones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  objetivo_id INT NOT NULL,
  version INT NOT NULL,
  texto TEXT NOT NULL,
  motivo VARCHAR(300) NOT NULL,
  curso TINYINT NOT NULL,
  autor_id INT NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (objetivo_id, version),
  FOREIGN KEY (objetivo_id) REFERENCES objetivos(id) ON DELETE CASCADE,
  FOREIGN KEY (autor_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS actas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  proyecto_id INT NOT NULL,
  numero INT NOT NULL,
  curso TINYINT NOT NULL,
  fecha DATE NOT NULL,
  autor_id INT NOT NULL,
  temas TEXT NOT NULL,
  compromisos TEXT NULL,
  UNIQUE (proyecto_id, numero),
  FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
  FOREIGN KEY (autor_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Cada fila es una versión del PDF subido para un entregable del catálogo
CREATE TABLE IF NOT EXISTS entregables (
  id INT AUTO_INCREMENT PRIMARY KEY,
  proyecto_id INT NOT NULL,
  def_id INT NOT NULL,
  curso TINYINT NOT NULL,
  version INT NOT NULL,
  archivo VARCHAR(255) NOT NULL,
  descripcion TEXT NULL,
  estado ENUM('Entregado','Revisado','Para corrección','Aprobado') NOT NULL DEFAULT 'Entregado',
  nota DECIMAL(2,1) NULL,
  autor_id INT NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (proyecto_id, def_id, version),
  FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
  FOREIGN KEY (def_id) REFERENCES entregables_def(id),
  FOREIGN KEY (autor_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Revisiones de los asesores sobre una versión del entregable (técnica = sin nota)
CREATE TABLE IF NOT EXISTS revisiones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  entregable_id INT NOT NULL,
  proyecto_id INT NOT NULL,
  acta_id INT NULL,
  tipo ENUM('tecnica','metodologica') NOT NULL,
  estado ENUM('Revisado','Para corrección','Aprobado') NOT NULL,
  nota DECIMAL(2,1) NULL,
  observaciones TEXT NULL,
  correcciones TEXT NULL,
  pdf VARCHAR(255) NULL,
  autor_id INT NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (entregable_id) REFERENCES entregables(id) ON DELETE CASCADE,
  FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
  FOREIGN KEY (acta_id) REFERENCES actas(id) ON DELETE SET NULL,
  FOREIGN KEY (autor_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS comentarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  proyecto_id INT NOT NULL,
  sobre ENUM('proyecto','entregable','acta') NOT NULL DEFAULT 'proyecto',
  sobre_id INT NULL,
  curso TINYINT NOT NULL DEFAULT 1,
  autor_id INT NOT NULL,
  texto TEXT NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
  FOREIGN KEY (autor_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS historial (
  id INT AUTO_INCREMENT PRIMARY KEY,
  proyecto_id INT NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  curso TINYINT NOT NULL,
  autor_id INT NOT NULL,
  tipo VARCHAR(40) NOT NULL,
  detalle VARCHAR(500) NOT NULL,
  FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
  FOREIGN KEY (autor_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
