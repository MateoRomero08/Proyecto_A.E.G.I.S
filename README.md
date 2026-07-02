# A.E.G.I.S

Plataforma web B2B de GRC enfocada en ISO 27001 para gestionar implementación de controles, evidencias, auditorías, capacitación, reportes y trazabilidad operativa por empresa.

A.E.G.I.S. está pensada para escenarios multi-tenant con roles diferenciados, control de acceso basado en permisos y una capa de seguridad alineada con buenas prácticas de ISO 27001 y OWASP Top 10.

## Resumen

El proyecto está dividido en dos aplicaciones principales:

- Backend REST en Django + Django REST Framework.
- Frontend SPA en React + TypeScript + Vite.

La arquitectura separa claramente la lógica de negocio, la autenticación JWT, el RBAC y la interfaz de usuario para que cada módulo pueda crecer de forma independiente sin perder control sobre permisos, trazabilidad o aislamiento por empresa.

## Funcionalidades Principales

- Gestión de empresas y usuarios por tenant.
- Implementación de controles ISO 27001 con evaluación y carga de evidencias.
- Solicitud de revisión sobre controles completados para activar el flujo de auditoría.
- Procesos de auditoría con revisiones, snapshots históricos, archivado y restauración.
- Capacitación con cursos, módulos, progreso por usuario y certificados PDF.
- Reportes centralizados en PDF para cumplimiento, auditoría, accesos, capacitación, forense y certificados.
- Centro de notificaciones para avisar a auditores cuando se solicita revisión.
- Bitácora de seguridad inmutable para trazabilidad administrativa.
- Paneles y rutas protegidas según rol y permisos.

## Arquitectura

### Backend

El backend expone una API REST con Django 6.0.3 y Django REST Framework. La autenticación se basa en JWT mediante SimpleJWT y el acceso a los endpoints protegidos parte de `IsAuthenticated` por defecto.

Apps principales:

- `usuarios`: autenticación, perfil, aprobación de usuarios, equipo, notificaciones y bitácora de seguridad.
- `implementacion`: empresas, controles ISO, evaluaciones de control y evidencias.
- `auditoria`: procesos de auditoría, revisiones y consultas de evaluaciones.
- `capacitacion`: cursos, módulos de contenido y progreso de usuarios.
- `reportes`: generación de PDFs y exportables.

### Frontend

El frontend es una SPA construida con React 18, TypeScript, Vite y Tailwind CSS 4. Usa React Router para navegación, Sonner para notificaciones y una colección de componentes UI modernos para dashboard, formularios y modales.

## Stack Tecnológico

| Capa | Tecnologías |
| --- | --- |
| Backend | Python, Django 6, Django REST Framework, SimpleJWT, CORS Headers, WhiteNoise, Gunicorn |
| Base de datos | PostgreSQL 15 en Docker; SQLite como respaldo local si no se define `DATABASE_URL` |
| Reportes | xhtml2pdf |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS 4 |
| UI | Radix UI, MUI, Lucide, Sonner, Recharts, Motion |
| Seguridad | JWT, RBAC, CSP, HSTS, CSRF/CORS configurables |

## Roles Y Permisos

Roles canónicos del sistema:

- `EMPLEADO`
- `IMPLEMENTADOR`
- `AUDITOR`
- `LIDER_EQUIPO`
- `CAPACITADOR`
- `ADMIN_SISTEMA`

Además, `is_superuser` funciona como perfil global de infraestructura y tiene prioridad absoluta sobre el resto de reglas de rol.

Notas importantes:

- `AUDITOR_INTERNO` sigue existiendo como compatibilidad histórica, pero se normaliza a `AUDITOR`.
- `ADMIN_SISTEMA` y `is_superuser` no deben quedar asociados a una empresa.
- La interfaz frontend y el backend comparten una matriz de permisos, pero la autoridad real siempre está en el backend.

## Módulos De Negocio

### Implementación ISO

Permite gestionar empresas, controles ISO, evaluaciones de control y evidencias. Desde este flujo se puede marcar el estado de cada control y solicitar revisión una vez que la implementación esté lista.

### Auditoría

Administra procesos de auditoría, revisiones por control, snapshots históricos y operaciones de archivado/restauración para mantener visibilidad sin perder trazabilidad.

### Capacitación

Incluye cursos, módulos y progreso por usuario. También soporta la descarga de certificados cuando el curso está completado.

### Usuarios Y Equipo

Incluye login, registro, perfil, cambio de contraseña, aprobación o rechazo de miembros del equipo, gestión global de usuarios y notificaciones internas.

### Reportes

Centraliza la generación de documentos PDF para cumplimiento, accesos, auditorías, capacitación, reportes forenses y certificados.

## Seguridad Y Trazabilidad

A.E.G.I.S. incorpora varias medidas pensadas para un contexto ISO 27001:

- Autenticación JWT con refresh token.
- CORS y CSRF configurables desde variables de entorno.
- Política de contenido y encabezados de seguridad en Django.
- RBAC por rol y por permisos explícitos.
- Aislamiento multi-tenant por empresa.
- Bitácora de seguridad inmutable para operaciones críticas.
- Snapshots y snapshots históricos en auditoría.
- Notificaciones para flujos de revisión y auditoría.
- Protección de rutas en frontend y backend.

## Rutas Principales

Backend expone prefijos principales bajo `/api/`:

- `/api/usuarios/`
- `/api/implementacion/`
- `/api/auditoria/`
- `/api/capacitacion/`
- `/api/reportes/`
- `/api/dashboard/stats/`

Frontend navega con estas rutas principales:

- `/`
- `/login`
- `/registro`
- `/espera`
- `/dashboard`
- `/dashboard/implementacion`
- `/dashboard/auditorias`
- `/dashboard/auditoria/proceso/:id`
- `/dashboard/usuarios`
- `/dashboard/equipo`
- `/dashboard/reportes`
- `/dashboard/capacitacion`

## Requisitos

- Python 3.12 o superior recomendado para el backend.
- Node.js 20 o superior recomendado para el frontend.
- PostgreSQL 15 si vas a usar la base de datos en local o por Docker.
- npm para instalar dependencias del frontend.

## Variables De Entorno

El proyecto carga variables desde `.env` en la raíz o dentro de `Backend/`.

### Backend

Variables más importantes:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `CORS_ALLOWED_ORIGINS`
- `CORS_ALLOW_ALL_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `RENDER_EXTERNAL_HOSTNAME`
- `USE_X_FORWARDED_HOST`
- `SECURE_SSL_REDIRECT`
- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`
- `CSRF_COOKIE_HTTPONLY`
- `SECURE_HSTS_SECONDS`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `SECURE_HSTS_PRELOAD`

Ejemplo mínimo para desarrollo local:

```env
SECRET_KEY=tu-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://aegis_user:aegis_password@localhost:5432/aegis_db
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
```

### Frontend

Variables útiles:

- `VITE_API_URL` para apuntar al backend.
- `VITE_API_ALLOWED_ORIGINS` para permitir orígenes adicionales en llamadas a la API.

Ejemplo:

```env
VITE_API_URL=http://localhost:8000
VITE_API_ALLOWED_ORIGINS=http://localhost:8000
```

## Instalación Local

### 1. Clonar el repositorio

```bash
git clone <URL-DE-TU-REPOSITORIO>
cd Proyecto_A.E.G.I.S
```

### 2. Levantar PostgreSQL con Docker

El archivo `docker-compose.yml` del proyecto solo crea el servicio de base de datos.

```bash
docker compose up -d
```

### 3. Preparar el backend

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

Si quieres cargar datos iniciales o roles, el backend incluye comandos de gestión útiles:

```bash
python manage.py setup_roles
python manage.py seed_grupos_permisos_aegis
python manage.py poblar_controles
python manage.py seed_capacitacion_inicial
python manage.py poblar_produccion
python manage.py limpiar_empresa_roles_globales
```

### 4. Arrancar el backend

```bash
python manage.py runserver
```

Por defecto quedará disponible en `http://localhost:8000`.

### 5. Preparar el frontend

```bash
cd ../Frontend
npm install
npm run dev
```

El frontend suele quedar disponible en `http://localhost:5173`.

## Comandos Útiles

### Backend

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend

```bash
npm run dev
npm run build
npm run preview
```

## Estructura Del Proyecto

```text
Proyecto_A.E.G.I.S/
├── Backend/
│   ├── core/
│   ├── usuarios/
│   ├── implementacion/
│   ├── auditoria/
│   ├── capacitacion/
│   ├── reportes/
│   └── media/
├── Frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── styles/
│   │   └── utils/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Endpoints Destacados

### Usuarios

- `POST /api/usuarios/registro/`
- `POST /api/usuarios/login/`
- `POST /api/usuarios/token/refresh/`
- `POST /api/usuarios/logout/`
- `GET /api/usuarios/perfil/`
- `PATCH /api/usuarios/perfil/actualizar/`
- `POST /api/usuarios/cambiar-password/`
- `GET /api/usuarios/empresa/`
- `GET /api/usuarios/equipo/`
- `POST /api/usuarios/equipo/<id>/aprobar/`
- `POST /api/usuarios/equipo/<id>/rechazar/`
- `GET /api/usuarios/bitacora/`
- `GET /api/usuarios/global/`
- `GET /api/usuarios/notificaciones/`

### Implementación

- `GET/POST /api/implementacion/empresas/`
- `GET/POST /api/implementacion/controles/`
- `GET/POST /api/implementacion/evaluaciones/`
- `GET/POST /api/implementacion/evidencias/`

### Auditoría

- `GET/POST /api/auditoria/procesos/`
- `GET/POST /api/auditoria/revisiones/`
- `GET /api/auditoria/evaluaciones/`

### Capacitación

- `GET/POST /api/capacitacion/cursos/`
- `GET/POST /api/capacitacion/modulos/`
- `GET/POST /api/capacitacion/progresos/`

### Reportes

- `GET /api/reportes/cumplimiento/`
- `GET /api/reportes/accesos/`
- `GET /api/reportes/auditoria/<id>/`
- `GET /api/reportes/capacitacion/usuarios/`
- `GET /api/reportes/capacitacion/usuario/<id>/`
- `GET /api/reportes/forense/`
- `GET /api/reportes/certificado/<id>/`

## Notas De Despliegue

- En producción conviene definir `DATABASE_URL` a PostgreSQL y no depender de SQLite.
- El backend ya incluye WhiteNoise y encabezados de seguridad para servir estáticos de forma más segura.
- Si despliegas en un entorno con proxy, revisa `RENDER_EXTERNAL_HOSTNAME` y `USE_X_FORWARDED_HOST`.
- El frontend debe apuntar al backend correcto mediante `VITE_API_URL`.
- El almacenamiento de media se sirve desde `/media/` en desarrollo.

## Licencia

Este proyecto no incluye una licencia explícita en el repositorio. Si vas a publicarlo en GitHub, conviene agregar una licencia antes de abrirlo a contribuciones externas.
