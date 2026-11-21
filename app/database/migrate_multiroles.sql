-- Migración: Soporte multi-rol (ejecutar una sola vez en la BD existente)
-- 1. Agregar columna rol_activo a sesiones
ALTER TABLE sesiones ADD COLUMN IF NOT EXISTS rol_activo VARCHAR(40) NULL;

-- 2. Crear tabla usuario_roles si no existe
CREATE TABLE IF NOT EXISTS usuario_roles (
  usuario_id INT NOT NULL,
  rol ENUM('estudiante','docente','administrador','asesor_tecnico','asesor_metodologico','jurado') NOT NULL,
  PRIMARY KEY (usuario_id, rol),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Poblar usuario_roles desde el rol legacy de cada usuario
INSERT IGNORE INTO usuario_roles (usuario_id, rol)
SELECT id, rol FROM usuarios WHERE rol IN ('estudiante','docente','administrador');

-- Para docentes: por defecto se les asignan los 3 roles docentes
-- (el admin puede refinarlos después desde la UI)
INSERT IGNORE INTO usuario_roles (usuario_id, rol)
SELECT id, 'asesor_tecnico' FROM usuarios WHERE rol = 'docente';
INSERT IGNORE INTO usuario_roles (usuario_id, rol)
SELECT id, 'asesor_metodologico' FROM usuarios WHERE rol = 'docente';
INSERT IGNORE INTO usuario_roles (usuario_id, rol)
SELECT id, 'jurado' FROM usuarios WHERE rol = 'docente';
