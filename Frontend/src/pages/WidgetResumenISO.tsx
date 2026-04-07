import { ClipboardCheck, FileCheck, Shield } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { DashboardStatsResponse } from "../utils/dashboardApi";

interface WidgetResumenISOProps {
  rol: string;
  stats?: DashboardStatsResponse | null;
  isLoading?: boolean;
  onAbrirImplementacion?: () => void;
  onAbrirAuditorias?: () => void;
  onExportarCumplimiento?: () => void;
}

const CHART_COLORS = ['#16A34A', '#EA580C', '#64748B', '#CBD5E1'];

export function WidgetResumenISO({
  rol,
  stats,
  isLoading = false,
  onAbrirImplementacion,
  onAbrirAuditorias,
  onExportarCumplimiento,
}: WidgetResumenISOProps) {
  const controlesImplementados = stats?.controles_implementados || 0;
  const controlesEnProceso = stats?.controles_en_proceso || 0;
  const totalControles = stats?.total_controles || 0;
  const controlesPendientes = stats?.controles_pendientes || 0;
  const controlesOtrosEvaluados = Math.max(
    totalControles - controlesImplementados - controlesEnProceso - controlesPendientes,
    0,
  );
  const porcentaje = stats?.porcentaje_cumplimiento_iso || 0;
  const cursosActivos = stats?.cursos_activos || 0;

  const chartData = [
    { name: '100% Implementados', value: controlesImplementados },
    { name: 'En Proceso', value: controlesEnProceso },
    { name: 'Pendientes de evaluar', value: controlesPendientes },
    { name: 'Otros evaluados', value: controlesOtrosEvaluados },
  ];

  return (
    <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-bold text-gray-900">Resumen de Cumplimiento ISO</h3>
          <p className="text-sm text-gray-600 mt-1">
            Vista operativa para el rol <span className="font-semibold">{rol}</span>.
          </p>
        </div>
        <Shield className="w-7 h-7 text-blue-600" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mt-5">
        <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3">
          <p className="text-xs text-blue-700 uppercase tracking-wide">Cumplimiento ISO</p>
          <p className="text-2xl font-bold text-blue-900 mt-1">{isLoading ? '...' : `${porcentaje}%`}</p>
        </div>
        <div className="rounded-lg border border-orange-200 bg-orange-50 px-4 py-3">
          <p className="text-xs text-orange-700 uppercase tracking-wide">En Proceso</p>
          <p className="text-2xl font-bold text-orange-900 mt-1">{isLoading ? '...' : controlesEnProceso}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
          <p className="text-xs text-slate-600 uppercase tracking-wide">Pendientes de evaluar</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{isLoading ? '...' : controlesPendientes}</p>
        </div>
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3">
          <p className="text-xs text-emerald-700 uppercase tracking-wide">Cursos activos</p>
          <p className="text-2xl font-bold text-emerald-900 mt-1">{isLoading ? '...' : cursosActivos}</p>
        </div>
      </div>

      <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-semibold text-slate-800">Distribución de estados de controles</p>
          <p className="text-xs text-slate-500">Total: {isLoading ? '...' : totalControles}</p>
        </div>

        {isLoading ? (
          <div className="h-[180px] flex items-center justify-center text-sm text-slate-500">Cargando gráfico...</div>
        ) : totalControles === 0 ? (
          <div className="h-[180px] flex items-center justify-center text-sm text-slate-500">
            No hay controles registrados para calcular cumplimiento.
          </div>
        ) : (
          <div className="h-[180px] mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={44}
                  outerRadius={70}
                  paddingAngle={2}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`iso-cell-${entry.name}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`${value}`, 'Controles']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2 mt-5">
        {onExportarCumplimiento && (
          <button
            onClick={onExportarCumplimiento}
            className="inline-flex items-center gap-2 bg-yellow-400 text-black font-semibold py-2 px-3 rounded-lg hover:bg-yellow-500"
          >
            <FileCheck className="w-4 h-4" />
            Exportar Estado de Cumplimiento
          </button>
        )}

        {onAbrirImplementacion && (
          <button
            onClick={onAbrirImplementacion}
            className="inline-flex items-center gap-2 bg-slate-900 text-white font-semibold py-2 px-3 rounded-lg hover:bg-black"
          >
            <FileCheck className="w-4 h-4" />
            Ir a implementación
          </button>
        )}

        {onAbrirAuditorias && (
          <button
            onClick={onAbrirAuditorias}
            className="inline-flex items-center gap-2 bg-blue-600 text-white font-semibold py-2 px-3 rounded-lg hover:bg-blue-700"
          >
            <ClipboardCheck className="w-4 h-4" />
            Ir a auditorías
          </button>
        )}
      </div>
    </section>
  );
}
