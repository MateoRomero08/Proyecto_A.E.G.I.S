import { GraduationCap, Settings2, Users } from "lucide-react";
import type { DashboardStatsResponse } from "../utils/dashboardApi";

interface WidgetAdminGlobalProps {
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

export function WidgetAdminGlobal({ onNavigate, stats, isLoading = false }: WidgetAdminGlobalProps) {
  return (
    <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Panel Global de Aegis</h2>
        <p className="text-sm text-gray-600 mt-1">
          Vista exclusiva de SuperAdmin para gobernanza de usuarios, equipos y capacitación global.
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-5">
        <button
          onClick={() => onNavigate('/dashboard/usuarios')}
          className="text-left rounded-lg border border-gray-200 bg-slate-50 hover:bg-slate-100 transition-colors p-4"
        >
          <Users className="w-5 h-5 text-slate-700" />
          <p className="font-semibold text-gray-900 mt-2">Usuarios Globales</p>
          <p className="text-xs text-gray-600 mt-1">Alta, baja y trazabilidad de identidades.</p>
        </button>

        <button
          onClick={() => onNavigate('/dashboard/equipo')}
          className="text-left rounded-lg border border-gray-200 bg-slate-50 hover:bg-slate-100 transition-colors p-4"
        >
          <Settings2 className="w-5 h-5 text-slate-700" />
          <p className="font-semibold text-gray-900 mt-2">Equipos Multi-tenant</p>
          <p className="text-xs text-gray-600 mt-1">Supervisión de flujos de aprobación por empresa.</p>
        </button>

        <button
          onClick={() => onNavigate('/dashboard/capacitacion')}
          className="text-left rounded-lg border border-gray-200 bg-slate-50 hover:bg-slate-100 transition-colors p-4"
        >
          <GraduationCap className="w-5 h-5 text-slate-700" />
          <p className="font-semibold text-gray-900 mt-2">Catálogo Aegis</p>
          <p className="text-xs text-gray-600 mt-1">Gestión del contenido oficial para todos los tenants.</p>
        </button>
      </div>
    </section>
  );
}
