import { createBrowserRouter } from "react-router-dom";
import { LandingPage } from "../pages/LandingPage";
import { Login } from "../pages/Login";
import { Registro } from "../pages/Registro";
import { EsperaAprobacion } from "../pages/EsperaAprobacion";
import { DashboardLayout } from "../pages/DashboardLayout";
import { Dashboard } from "../pages/Dashboard";
import { ImplementacionISO } from "../pages/ImplementacionISO";
import { ListaAuditorias } from "../pages/ListaAuditorias";
import { Auditoria } from "../pages/Auditoria";
import { GestionUsuarios } from "../pages/GestionUsuarios";
import { GestionEquipo } from "../pages/GestionEquipo";
import { Reportes } from "../pages/Reportes";
import { Capacitacion } from "../pages/Capacitacion";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { PERMISOS_FRONTEND } from "../utils/auth";

/**
 * Configuración del enrutador de la aplicación.
 * 
 * Rutas públicas:
 * - / (Landing)
 * - /login
 * - /registro
 * 
 * Rutas privadas (protegidas con ProtectedRoute):
 * - /dashboard (y todas sus subrutas)
 *   - /dashboard
 *   - /dashboard/implementacion
 *   - /dashboard/auditorias (lista de procesos de auditoría)
 *   - /dashboard/auditoria/proceso/:id (ejecución de auditoría)
 *   - /dashboard/usuarios
 *   - /dashboard/reportes
 *   - /dashboard/capacitacion
 */
export const router = createBrowserRouter([
  // ===== RUTAS PÚBLICAS =====
  {
    path: "/",
    Component: LandingPage,
  },
  {
    path: "/login",
    Component: Login,
  },
  {
    path: "/registro",
    Component: Registro,
  },
  {
    path: "/espera",
    element: (
      <ProtectedRoute>
        <EsperaAprobacion />
      </ProtectedRoute>
    ),
  },
  
  // ===== RUTAS PRIVADAS (PROTEGIDAS) =====
  {
    path: "/dashboard",
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: (
          <ProtectedRoute permission={PERMISOS_FRONTEND.VER_DASHBOARD}>
            <Dashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: "implementacion",
        element: (
          <ProtectedRoute permission={PERMISOS_FRONTEND.VER_IMPLEMENTACION}>
            <ImplementacionISO />
          </ProtectedRoute>
        ),
      },
      {
        path: "auditorias",
        element: (
          <ProtectedRoute permission={PERMISOS_FRONTEND.VER_AUDITORIA}>
            <ListaAuditorias />
          </ProtectedRoute>
        ),
      },
      {
        path: "auditoria/proceso/:id",
        element: (
          <ProtectedRoute permission={PERMISOS_FRONTEND.VER_AUDITORIA}>
            <Auditoria />
          </ProtectedRoute>
        ),
      },
      {
        path: "usuarios",
        element: (
          <ProtectedRoute permission={PERMISOS_FRONTEND.VER_USUARIOS_GLOBALES}>
            <GestionUsuarios />
          </ProtectedRoute>
        ),
      },
      {
        path: "equipo",
        element: (
          <ProtectedRoute permission={PERMISOS_FRONTEND.VER_EQUIPO}>
            <GestionEquipo />
          </ProtectedRoute>
        ),
      },
      {
        path: "reportes",
        element: (
          <ProtectedRoute permission={PERMISOS_FRONTEND.VER_REPORTES}>
            <Reportes />
          </ProtectedRoute>
        ),
      },
      {
        path: "capacitacion",
        element: (
          <ProtectedRoute permission={PERMISOS_FRONTEND.VER_CAPACITACION}>
            <Capacitacion />
          </ProtectedRoute>
        ),
      },
    ],
  },
]);
