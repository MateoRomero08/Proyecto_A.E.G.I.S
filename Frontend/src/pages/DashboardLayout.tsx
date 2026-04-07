import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";
import {
  Shield,
  LayoutDashboard,
  FileCheck,
  ClipboardList,
  Users,
  UserCheck,
  FileText,
  GraduationCap,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { cerrarSesionRemota, esSuperusuario, obtenerRolUsuario, obtenerUsuario, PERMISOS_FRONTEND } from "../utils/auth";
import { RoleBadge, obtenerClasesAvatarRol } from "../components/RoleBadge";
import { usePermissions } from "../hooks/usePermissions";

const obtenerInicialesUsuario = (nombre?: string, email?: string, username?: string): string => {
  const fuente = (nombre && nombre.trim())
    || (email && email.trim().split("@")[0])
    || (username && username.trim())
    || "U";

  const partes = fuente
    .replace(/[._-]+/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (partes.length >= 2) {
    return `${partes[0][0]}${partes[1][0]}`.toUpperCase();
  }

  return fuente.slice(0, 2).toUpperCase();
};

export function DashboardLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarAbiertoMovil, setSidebarAbiertoMovil] = useState(false);
  const esSuperAdmin = esSuperusuario();
  const rol = obtenerRolUsuario();
  const usuarioActual = obtenerUsuario();
  const { hasPermission } = usePermissions(usuarioActual);

  const nombreCompleto = `${String(usuarioActual?.first_name || "")} ${String(usuarioActual?.last_name || "")}`.trim();
  const nombrePerfil =
    String(usuarioActual?.full_name || "").trim()
    || nombreCompleto
    || String(usuarioActual?.email || "").trim()
    || String(usuarioActual?.username || "").trim()
    || "Usuario";
  const esLiderVisual = Boolean(!esSuperAdmin && (rol === "LIDER_EQUIPO" || usuarioActual?.es_administrador_empresa));
  const clasesAvatarRol = obtenerClasesAvatarRol(rol, esSuperAdmin, esLiderVisual);
  const inicialesPerfil = obtenerInicialesUsuario(nombreCompleto || nombrePerfil, usuarioActual?.email, usuarioActual?.username);

  const menuItems = (() => {
    const dashboardItem = { path: "/dashboard", icon: LayoutDashboard, label: "Dashboard", permission: PERMISOS_FRONTEND.VER_DASHBOARD };

    if (esSuperAdmin) {
      return [
        dashboardItem,
        { path: "/dashboard/usuarios", icon: Users, label: "Gestión de Usuarios", permission: PERMISOS_FRONTEND.VER_USUARIOS_GLOBALES },
        { path: "/dashboard/equipo", icon: UserCheck, label: "Gestión de Equipos (Global)", permission: PERMISOS_FRONTEND.VER_EQUIPO },
        { path: "/dashboard/reportes", icon: FileText, label: "Reportes (Global)", permission: PERMISOS_FRONTEND.VER_REPORTES },
        { path: "/dashboard/capacitacion", icon: GraduationCap, label: "Capacitación (Global)", permission: PERMISOS_FRONTEND.VER_CAPACITACION },
      ].filter((item) => hasPermission(item.permission));
    }

    return [
      dashboardItem,
      { path: "/dashboard/equipo", icon: UserCheck, label: "Gestión de Equipo (Local)", permission: PERMISOS_FRONTEND.VER_EQUIPO },
      { path: "/dashboard/reportes", icon: FileText, label: "Reportes", permission: PERMISOS_FRONTEND.VER_REPORTES },
      { path: "/dashboard/implementacion", icon: FileCheck, label: "Implementación ISO 27001", permission: PERMISOS_FRONTEND.VER_IMPLEMENTACION },
      { path: "/dashboard/auditorias", icon: ClipboardList, label: "Auditoría", permission: PERMISOS_FRONTEND.VER_AUDITORIA },
      { path: "/dashboard/capacitacion", icon: GraduationCap, label: "Capacitación", permission: PERMISOS_FRONTEND.VER_CAPACITACION },
    ].filter((item) => hasPermission(item.permission));
  })();

  const handleLogout = async () => {
    await cerrarSesionRemota();
    navigate("/login");
  };

  const navegar = (path: string) => {
    navigate(path);
    setSidebarAbiertoMovil(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <header className="fixed top-0 left-0 right-0 h-14 bg-gray-900 text-white border-b border-gray-800 z-50 lg:hidden">
        <div className="h-full px-4 flex items-center justify-between">
          <button
            onClick={() => setSidebarAbiertoMovil((prev) => !prev)}
            className="inline-flex items-center justify-center w-9 h-9 rounded-md hover:bg-gray-800"
            aria-label="Abrir menú"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="inline-flex items-center gap-2 font-bold tracking-wide">
            <Shield className="w-4 h-4 text-yellow-400" />
            AEGIS
          </div>

          <div className="w-9 h-9" />
        </div>
      </header>

      {sidebarAbiertoMovil && (
        <button
          type="button"
          aria-label="Cerrar menú"
          onClick={() => setSidebarAbiertoMovil(false)}
          className="fixed inset-0 bg-black/45 z-40 lg:hidden"
        />
      )}

      {/* Sidebar - Fijo y Permanente */}
      <aside
        className={`fixed top-0 left-0 h-screen w-64 bg-gray-900 text-white flex flex-col z-50 transform transition-transform duration-200 ease-out lg:translate-x-0 ${
          sidebarAbiertoMovil ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Logo */}
        <div className="p-6 flex items-center gap-3 border-b border-gray-800">
          <div className="w-10 h-10 bg-yellow-400 rounded-lg flex items-center justify-center">
            <Shield className="w-6 h-6 text-black" />
          </div>
          <span className="font-bold text-xl">AEGIS</span>

          <button
            onClick={() => setSidebarAbiertoMovil(false)}
            className="ml-auto inline-flex lg:hidden items-center justify-center w-8 h-8 rounded-md text-gray-300 hover:bg-gray-800 hover:text-white"
            aria-label="Cerrar menú lateral"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Menu - Área scrolleable */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              location.pathname === item.path ||
              (item.path === "/dashboard/auditorias" &&
                location.pathname.startsWith("/dashboard/auditoria/proceso/"));
            
            return (
              <button
                key={item.path}
                onClick={() => navegar(item.path)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? "bg-yellow-400 text-black font-semibold"
                    : "text-gray-300 hover:bg-gray-800 hover:text-white"
                }`}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Perfil + Cerrar Sesion - Siempre visible al final */}
        <div className="p-4 border-t border-gray-800 mt-auto">
          <div className="mb-3 rounded-lg border border-gray-700 bg-gray-800/60 px-3 py-2.5 flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${clasesAvatarRol}`}>
              {inicialesPerfil}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-white truncate">{nombrePerfil}</p>
              <RoleBadge rol={rol} isSuperuser={esSuperAdmin} isLeader={esLiderVisual} className="mt-1" />
            </div>
          </div>

          <button
            onClick={() => {
              void handleLogout();
            }}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-red-900/50 hover:text-white transition-colors"
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            <span>Cerrar sesión</span>
          </button>
        </div>
      </aside>

      {/* Contenido Principal - Con margen izquierdo para no quedar detrás del sidebar */}
      <main className="flex-1 lg:ml-64 overflow-auto w-full">
        <div className="p-4 sm:p-6 lg:p-8 pt-20 lg:pt-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
