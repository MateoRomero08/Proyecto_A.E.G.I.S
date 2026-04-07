---
description: Reglas globales y contexto arquitectónico para el desarrollo del proyecto Aegis (Plataforma GRC Full Stack).
# applyTo: '**/*' # Se aplica a todos los archivos del proyecto
---

# Contexto del Proyecto: A.E.G.I.S
Aegis es una plataforma web B2B de GRC (Governance, Risk, and Compliance) diseñada para ayudar a las empresas (hasta 200 empleados en su fase MVP) a implementar, auditar, capacitar y gestionar la norma ISO 27001.
El objetivo principal es manejar evidencias, controles de seguridad y auditorías de forma estructurada, escalable y altamente segura.

# Arquitectura General
El proyecto sigue una arquitectura desacoplada:
1.  **Backend:** API REST construida con Python, Django y Django REST Framework (DRF).
2.  **Frontend:** Single Page Application (SPA) construida con React, TypeScript y Vite.

---

# Reglas de Backend (Python / Django)
* **Paradigma:** Utiliza Programación Orientada a Objetos (POO) estricta para los modelos y vistas basadas en clases (Class-Based Views) en DRF cuando sea posible.
* **Desarrollo Guiado por Modelos (Model-Driven):** La base de datos es la prioridad. Define primero los modelos (`models.py`) con sus relaciones (ForeignKey, ManyToMany) antes de escribir la lógica de negocio o los serializadores.
* **Base de Datos:** Asume PostgreSQL como motor principal. Escribe consultas eficientes utilizando el ORM de Django (usa `select_related` y `prefetch_related` para evitar el problema de consultas N+1).
* **Documentación de API:** Sigue los estándares RESTful para nombrar los endpoints (ej. `/api/empresas/`, `/api/auditorias/`).

# Reglas de Frontend (React / TypeScript)
* **Paradigma:** Utiliza Programación Funcional. Usa componentes funcionales de React y Hooks (`useState`, `useEffect`, etc.). **Cero componentes de clase.**
* **Tipado:** Usa TypeScript estricto. Define `interfaces` o `types` para todas las respuestas esperadas de la API de Django. Evita a toda costa el uso de `any`.
* **Estilos:** El proyecto utiliza Tailwind CSS basado en una plantilla de Figma. Reutiliza clases utilitarias de Tailwind y mantén un diseño responsivo (mobile-first).
* **Comunicación con la API:** Centraliza todas las llamadas HTTP a la API de Django en una carpeta dedicada (ej. `src/services/`). No hagas fetch directamente dentro de los componentes visuales. Maneja siempre los estados de carga (loading) y error.
* Usa estrictamente los colores, variables y utilidades definidas en la configuración de Tailwind y en la carpeta src/styles/. No inventes paletas de colores nuevas.

# Seguridad y Autenticación (Crítico para ISO 27001)
* **OWASP Top 10:** Aplica principios de seguridad en todo momento. Valida y sanea todas las entradas de datos tanto en el frontend (React) como en el backend (Django).
* **Autenticación:** El sistema utiliza JWT (JSON Web Tokens). Incluye siempre el token en el header `Authorization: Bearer <token>` en las peticiones del frontend.
* **Autorización (RBAC):** Implementa un Control de Acceso Basado en Roles (Ej. Administrador, Auditor Interno, Auditor Externo). En el backend, asegúrate de que los endpoints verifiquen los permisos del usuario antes de devolver o modificar datos sensibles.

# Formato y Código Limpio
* Mantén los archivos pequeños y modulares.
* Usa nombres descriptivos en español para el dominio del negocio (ej. `Auditoria`, `Evidencia`, `ControlISO`), pero mantén el código estándar en inglés para verbos y programación (ej. `getAuditorias`, `isLoaded`, `fetchData`).
* Usa f-strings en Python para la interpolación de cadenas.
* Asegurate de usar siempre buenas prácticas.
* Refactoriza el codigo siempre que se pueda.
* Crea test de las funcionalidades principales.
