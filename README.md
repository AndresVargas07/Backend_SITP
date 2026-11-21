# Backend SITP · Sistema de Trazabilidad de Proyectos de Investigación Formativa

Backend desarrollado para la Universidad Cooperativa de Colombia (UCC - Campus Medellín).

## Arquitectura
Monolito modular por capas en **Python con Flask** y **MySQL**:
- **Controlador (`routes.py`):** Define endpoints y códigos HTTP.
- **DTO (`schemas.py`):** Valida, sanitiza y tipa datos de entrada.
- **Servicio (`service.py`):** Reglas de negocio y seguridad.
- **Repositorio / Modelo (`repository.py`):** Persistencia y SQL parametrizado.

## Módulos
- `auth`: Autenticación por token Bearer, sesiones y selector de rol (Role Switcher / Swap).
- `usuarios`: Administración de usuarios, asignaciones y multi-rol.
- `proyectos`: Ciclo de vida y trazabilidad a través de los tres cursos.
- `entregables`: Gestión de PDFs, versionamiento y revisiones técnicas/metodológicas.
- `actas`: Actas de reunión con compromisos y firma.
- `objetivos`: Objetivos generales y específicos con control de versiones.
- `evaluacion`: Evaluación con rúbrica para jurados.
- `seguimiento`: Historial de cambios y comentarios compartidos.
- `catalogo`: Cursos, programas, semestres y rúbricas.

## Instalación y Ejecución
1. Crear y activar entorno virtual:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # Windows
   # source .venv/bin/activate    # Linux / Mac
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Configurar variables de entorno:
   Copiar `.env.example` a `.env` y configurar credenciales de MySQL.
4. Iniciar servidor:
   ```bash
   python main.py
   ```
   El servidor iniciará en `http://localhost:8000`. Al arrancar, inicializa y migra la base de datos automáticamente.
