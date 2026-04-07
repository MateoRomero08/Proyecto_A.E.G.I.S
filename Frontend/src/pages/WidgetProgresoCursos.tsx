import { BookOpen, GraduationCap, PlayCircle } from "lucide-react";
import type { DashboardStatsResponse } from "../utils/dashboardApi";

interface WidgetProgresoCursosProps {
  stats?: DashboardStatsResponse | null;
  isLoading?: boolean;
  onAbrirCapacitacion: () => void;
}

export function WidgetProgresoCursos({
  stats,
  isLoading = false,
  onAbrirCapacitacion,
}: WidgetProgresoCursosProps) {
  const cursosPendientes = stats?.mis_cursos_pendientes || 0;
  const modulosCompletados = stats?.mis_modulos_completados || 0;
  const totalModulosActivos = stats?.total_modulos_activos || 0;
  const porcentajeAvance = totalModulosActivos > 0
    ? Math.round((modulosCompletados / totalModulosActivos) * 100)
    : 0;

  return (
    <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-bold text-gray-900">Progreso de Capacitación</h3>
          <p className="text-sm text-gray-600 mt-1">
            Revisa tus cursos pendientes y completa módulos para obtener tu certificado.
          </p>
        </div>
        <GraduationCap className="w-7 h-7 text-yellow-600" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-5">
        <div className="rounded-lg border border-gray-200 bg-slate-50 px-4 py-3">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Cursos pendientes</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{isLoading ? '...' : cursosPendientes}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-slate-50 px-4 py-3">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Módulos completados</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{isLoading ? '...' : modulosCompletados}</p>
        </div>
      </div>

      <div className="mt-4">
        <div className="flex items-center justify-between text-xs text-gray-600 mb-1.5">
          <span>Avance general por módulos</span>
          <span>{isLoading ? '...' : `${porcentajeAvance}%`}</span>
        </div>
        <div className="h-2.5 w-full rounded-full bg-gray-200 overflow-hidden">
          <div
            className="h-full rounded-full bg-yellow-400 transition-all"
            style={{ width: `${isLoading ? 0 : porcentajeAvance}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1.5">
          {isLoading ? 'Cargando módulos...' : `${modulosCompletados} de ${totalModulosActivos} módulos activos completados`}
        </p>
      </div>

      <button
        onClick={onAbrirCapacitacion}
        className="mt-5 inline-flex items-center gap-2 bg-yellow-400 text-black font-semibold py-2.5 px-4 rounded-lg hover:bg-yellow-500 transition-colors"
      >
        <PlayCircle className="w-4 h-4" />
        Continuar aprendizaje
      </button>

      <div className="mt-3 text-xs text-gray-500 inline-flex items-center gap-1.5">
        <BookOpen className="w-3.5 h-3.5" />
        La barra de avance se actualiza por cada módulo completado.
      </div>
    </section>
  );
}
