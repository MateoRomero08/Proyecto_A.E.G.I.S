import { FileText, GraduationCap, History, Settings2, Users } from "lucide-react";
import type { DashboardStatsResponse } from "../utils/dashboardApi";

interface WidgetAdminGlobalProps {
  modo: "SUPERADMIN" | "ADMIN_SISTEMA";
  onNavigate: (path: string) => void;
  stats?: DashboardStatsResponse | null;
  isLoading?: boolean;
}

const getMetricValue = (value: number | undefined, isLoading: boolean): string => {
  if (isLoading) {
    return '...';
  }

  return new Intl.NumberFormat('es-CL').format(value || 0);
};

export function WidgetAdminGlobal({ modo, onNavigate, stats, isLoading = false }: WidgetAdminGlobalProps) {
  const esSuperAdmin = modo === "SUPERADMIN";

  return (
    <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          {esSuperAdmin ? "Panel Global de Aegis" : "Panel Global de Administración"}
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          {esSuperAdmin
            ? "Vista de SuperAdmin para gobernanza global de usuarios, forense y reportes multi-tenant."
            : "Vista de ADMIN_SISTEMA para aprobación/rechazo global, bitácora forense y reportes globales."}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-5">
        <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3">
          <p className="text-xs text-blue-700 uppercase tracking-wide">Empresas registradas</p>
          <p className="text-3xl font-bold text-blue-900 mt-1">
            {getMetricValue(stats?.total_empresas, isLoading)}
          </p>
        </div>
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3">
          <p className="text-xs text-emerald-700 uppercase tracking-wide">Usuarios totales</p>
          <p className="text-3xl font-bold text-emerald-900 mt-1">
            {getMetricValue(stats?.total_usuarios, isLoading)}
          </p>
        </div>
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
          <p className="text-xs text-amber-700 uppercase tracking-wide">Cursos globales Aegis</p>
          <p className="text-3xl font-bold text-amber-900 mt-1">
            {getMetricValue(stats?.total_cursos_globales, isLoading)}
          </p>
        </div>
      </div>

      {esSuperAdmin ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 mt-5">
          <button
            onClick={() => onNavigate('/dashboard/usuarios')}
            className="text-left rounded-lg border border-gray-200 bg-slate-50 hover:bg-slate-100 transition-colors p-4"
          >
            <Users className="w-5 h-5 text-slate-700" />
            <p className="font-semibold text-gray-900 mt-2">G.U ADMIN</p>
            <p className="text-xs text-gray-600 mt-1">Alta, edición e inactivación controlada de identidades.</p>
          </button>

          <button
            onClick={() => onNavigate('/dashboard/usuarios?panel=bitacora')}
            className="text-left rounded-lg border border-gray-200 bg-slate-50 hover:bg-slate-100 transition-colors p-4"
          >
            <History className="w-5 h-5 text-slate-700" />
            <p className="font-semibold text-gray-900 mt-2">Bitácora Forense</p>
            <p className="text-xs text-gray-600 mt-1">Consulta WORM de eventos críticos de seguridad.</p>
          </button>

          <button
            onClick={() => onNavigate('/dashboard/equipo')}
            className="text-left rounded-lg border border-gray-200 bg-slate-50 hover:bg-slate-100 transition-colors p-4"
          >
            <Settings2 className="w-5 h-5 text-slate-700" />
            <p className="font-semibold text-gray-900 mt-2">Gestión Equipo GLOBAL</p>
            <p className="text-xs text-gray-600 mt-1">Aprobación/rechazo inter-tenant por empresa.</p>
          </button>

          <button
            onClick={() => onNavigate('/dashboard/reportes')}
            className="text-left rounded-lg border border-gray-200 bg-slate-50 hover:bg-slate-100 transition-colors p-4"
          >
            <FileText className="w-5 h-5 text-slate-700" />
            <p className="font-semibold text-gray-900 mt-2">Reportes Global</p>
            <p className="text-xs text-gray-600 mt-1">Exportación por tenant y trazabilidad ejecutiva.</p>
          </button>

          <button
            onClick={() => onNavigate('/dashboard/capacitacion')}
            className="text-left rounded-lg border border-gray-200 bg-slate-50 hover:bg-slate-100 transition-colors p-4"
          >
            <GraduationCap className="w-5 h-5 text-slate-700" />
            <p className="font-semibold text-gray-900 mt-2">Capacitación</p>
            <p className="text-xs text-gray-600 mt-1">Gestión del catálogo oficial AEGIS y seguimiento académico.</p>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 mt-5">
          <button
            onClick={() => onNavigate('/dashboard/equipo')}
            className="text-left rounded-lg border border-gray-200 bg-slate-50 hover:bg-slate-100 transition-colors p-4"
          >
            <Settings2 className="w-5 h-5 text-slate-700" />
            <p className="font-semibold text-gray-900 mt-2">Gestión Equipo GLOBAL</p>
            <p className="text-xs text-gray-600 mt-1">Aprobación/rechazo global de usuarios por tenant.</p>
          </button>

          <button
            onClick={() => onNavigate('/dashboard/usuarios?panel=bitacora')}
            className="text-left rounded-lg border border-gray-200 bg-slate-50 hover:bg-slate-100 transition-colors p-4"
          >
            <History className="w-5 h-5 text-slate-700" />
            <p className="font-semibold text-gray-900 mt-2">Bitácora Forense</p>
            <p className="text-xs text-gray-600 mt-1">Solo lectura de eventos inmutables de seguridad.</p>
          </button>

          <button
            onClick={() => onNavigate('/dashboard/reportes')}
            className="text-left rounded-lg border border-gray-200 bg-slate-50 hover:bg-slate-100 transition-colors p-4"
          >
            <FileText className="w-5 h-5 text-slate-700" />
            <p className="font-semibold text-gray-900 mt-2">Reportes Global</p>
            <p className="text-xs text-gray-600 mt-1">Consulta y previsualización de reportes globales.</p>
          </button>

          <button
            onClick={() => onNavigate('/dashboard/capacitacion')}
            className="text-left rounded-lg border border-gray-200 bg-slate-50 hover:bg-slate-100 transition-colors p-4"
          >
            <GraduationCap className="w-5 h-5 text-slate-700" />
            <p className="font-semibold text-gray-900 mt-2">Capacitación</p>
            <p className="text-xs text-gray-600 mt-1">Gestión de cursos oficiales y seguimiento por empresa.</p>
          </button>
        </div>
      )}
    </section>
  );
}
