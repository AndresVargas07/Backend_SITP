-- Esquema MySQL del SITP (Sistema de Trazabilidad de Proyectos de Investigación Formativa)
CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  -- Rol primario de cuenta (compatibilidad legacy) - los roles reales estan en usuario_roles
  rol ENUM('estudiante','docente','administrador') NOT NULL DEFAULT 'estudiante',
  programa VARCHAR(80) NULL,
  password_hash VARCHAR(255) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Multi-rol: un usuario puede tener varios roles simultáneos
CREATE TABLE IF NOT EXISTS usuario_roles (
  usuario_id INT NOT NULL,
  rol ENUM('estudiante','docente','administrador','asesor_tecnico','asesor_metodologico','jurado') NOT NULL,
  PRIMARY KEY (usuario_id, rol),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sesiones (
  token CHAR(64) PRIMARY KEY,
  usuario_id INT NOT NULL,
  expira DATETIME NOT NULL,
  -- Rol activo elegido por el usuario en esta sesión (Role Switcher)
  rol_activo VARCHAR(40) NULL,
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

-- Catálogos académicos administrables
CREATE TABLE IF NOT EXISTS programas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL UNIQUE,
  activo BOOLEAN NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS semestres (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(20) NOT NULL UNIQUE,
  activo BOOLEAN NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Rúbrica del jurado: criterios con peso (%)
CREATE TABLE IF NOT EXISTS criterios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  descripcion VARCHAR(300) NOT NULL,
  peso TINYINT NOT NULL
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
  jurado_id INT NULL,
  creado DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (asesor_tecnico_id) REFERENCES usuarios(id),
  FOREIGN KEY (asesor_metodologico_id) REFERENCES usuarios(id),
  FOREIGN KEY (jurado_id) REFERENCES usuarios(id)
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
  firmada BOOLEAN NOT NULL DEFAULT 0,
  firmada_por INT NULL,
  firmada_en DATETIME NULL,
  UNIQUE (proyecto_id, numero),
  FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
  FOREIGN KEY (autor_id) REFERENCES usuarios(id),
  FOREIGN KEY (firmada_por) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Compromisos de cada acta (descripción, responsable y fecha límite)
CREATE TABLE IF NOT EXISTS compromisos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  acta_id INT NOT NULL,
  descripcion VARCHAR(300) NOT NULL,
  responsable VARCHAR(120) NOT NULL,
  fecha_limite DATE NOT NULL,
  cumplido BOOLEAN NOT NULL DEFAULT 0,
  FOREIGN KEY (acta_id) REFERENCES actas(id) ON DELETE CASCADE
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

-- Evaluación por rúbrica del jurado (una por jurado y materia, puntajes en JSON {criterio_id: 0-5})
CREATE TABLE IF NOT EXISTS evaluaciones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  proyecto_id INT NOT NULL,
  jurado_id INT NOT NULL,
  curso TINYINT NOT NULL,
  puntajes TEXT NOT NULL,
  total DECIMAL(3,2) NOT NULL,
  concepto ENUM('Aprobado','Observado / Plan de mejora') NOT NULL,
  observaciones TEXT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE (proyecto_id, jurado_id, curso),
  FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
  FOREIGN KEY (jurado_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
