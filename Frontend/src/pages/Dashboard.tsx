import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BellRing, Check, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { apiFetch } from "../utils/api";
import { esAdminSistema, esSuperusuario, obtenerRolUsuario, obtenerUsuario } from "../utils/auth";
import { fetchDashboardStats, type DashboardStatsResponse } from "../utils/dashboardApi";
import { WidgetAdminGlobal } from "./WidgetAdminGlobal";
import { WidgetBienvenida } from "./WidgetBienvenida";
import { WidgetProgresoCursos } from "./WidgetProgresoCursos";
import { WidgetResumenISO } from "./WidgetResumenISO";

interface NotificacionInApp {
  id: number;
  titulo: string;
  mensaje: string;
  leida: boolean;
  fecha_creacion: string;
}

type NotificacionesResponse = NotificacionInApp[] | { results: NotificacionInApp[] };

const normalizeNotificaciones = (data: NotificacionesResponse): NotificacionInApp[] => {
  if (Array.isArray(data)) {
    return data;
  }
  return data?.results || [];
};

const parseApiError = (error: unknown, fallback: string): string => {
  if (!(error instanceof Error)) {
    return fallback;
  }

  const raw = error.message || fallback;
  const parts = raw.split(" - ");
  const payload = parts.length > 1 ? parts.slice(1).join(" - ") : raw;

  try {
    const parsed = JSON.parse(payload);
    if (typeof parsed === "string") {
      return parsed;
    }
    if (parsed?.detail) {
      return String(parsed.detail);
    }
  } catch {
    return raw;
  }

  return raw;
};

export function Dashboard() {
  const navigate = useNavigate();
  const usuario = obtenerUsuario();
  const [stats, setStats] = useState<DashboardStatsResponse | null>(null);
  const [cargandoStats, setCargandoStats] = useState(false);
  const [isRefreshingStats, setIsRefreshingStats] = useState(false);
  const [notificaciones, setNotificaciones] = useState<NotificacionInApp[]>([]);
  const [cargandoNotificaciones, setCargandoNotificaciones] = useState(false);
  const [actualizandoNotificacionId, setActualizandoNotificacionId] = useState<number | null>(null);

  const rolUsuario = obtenerRolUsuario();
  const esSuperAdmin = esSuperusuario();
  const esAdminGlobal = esAdminSistema();
  const esPerfilGlobal = esSuperAdmin || esAdminGlobal;
  const esAuditor = !esPerfilGlobal && rolUsuario === "AUDITOR";
  const nombreUsuario = (`${usuario?.first_name || ''} ${usuario?.last_name || ''}`).trim() || usuario?.username || "Usuario";
  const rolVisible = esSuperAdmin ? "SUPERADMIN" : (esAdminGlobal ? "ADMIN_SISTEMA" : (rolUsuario || "USUARIO"));
  const empresaNombre = usuario?.empresa_info?.nombre || null;
  const totalPendientes = useMemo(() => notificaciones.filter((n) => !n.leida).length, [notificaciones]);

  useEffect(() => {
    let mounted = true;

    const cargarStats = async (silencioso = false) => {
      if (silencioso) {
        setIsRefreshingStats(true);
      } else {
        setCargandoStats(true);
      }

      try {
        const data = await fetchDashboardStats();
        if (mounted) {
          setStats((prev) => {
            if (JSON.stringify(prev) === JSON.stringify(data)) {
              return prev;
            }
            return data;
          });
        }
      } catch (error) {
        if (!mounted) {
          return;
        }

        if (silencioso) {
          console.warn('No se pudieron refrescar silenciosamente las métricas del dashboard:', error);
          return;
        }

        if (mounted) {
          toast.error('No se pudieron cargar las métricas del dashboard', {
            description: parseApiError(error, 'Intenta nuevamente en unos segundos.'),
          });
        }
      } finally {
        if (mounted && !silencioso) {
          setCargandoStats(false);
        }

        if (mounted && silencioso) {
          setIsRefreshingStats(false);
        }
      }
    };

    void cargarStats(false);

    const intervalId = window.setInterval(() => {
      void cargarStats(true);
    }, 15000);

    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    if (!esAuditor) {
      return;
    }

    const cargarNotificaciones = async () => {
      setCargandoNotificaciones(true);
      try {
        const data = await apiFetch<NotificacionesResponse>('/usuarios/notificaciones/?leida=false');
        setNotificaciones(normalizeNotificaciones(data));
      } catch (error) {
        toast.error('No se pudieron cargar las notificaciones', {
          description: parseApiError(error, 'Intenta nuevamente en unos segundos.'),
        });
      } finally {
        setCargandoNotificaciones(false);
      }
    };

    cargarNotificaciones();
  }, [esAuditor]);

  const marcarComoLeida = async (notificacionId: number) => {
    setActualizandoNotificacionId(notificacionId);
    try {
      await apiFetch(`/usuarios/notificaciones/${notificacionId}/`, {
        method: 'PATCH',
        body: JSON.stringify({ leida: true }),
      });

      setNotificaciones((prev) => prev.filter((item) => item.id !== notificacionId));
    } catch (error) {
      toast.error('No se pudo actualizar la notificación', {
        description: parseApiError(error, 'Intenta nuevamente en unos segundos.'),
      });
    } finally {
      setActualizandoNotificacionId(null);
    }
  };

  const marcarTodasLeidas = async () => {
    setActualizandoNotificacionId(-1);
    try {
      await apiFetch('/usuarios/notificaciones/marcar-todas-leidas/', {
        method: 'POST',
      });
      setNotificaciones([]);
      toast.success('Notificaciones marcadas como leídas');
    } catch (error) {
      toast.error('No se pudieron marcar todas las notificaciones', {
        description: parseApiError(error, 'Intenta nuevamente en unos segundos.'),
      });
    } finally {
      setActualizandoNotificacionId(null);
    }
  };

  const widgets = useMemo(() => {
    if (esPerfilGlobal) {
      return [
        <WidgetAdminGlobal
          key="widget-admin-global"
          modo={esSuperAdmin ? "SUPERADMIN" : "ADMIN_SISTEMA"}
          onNavigate={(path) => navigate(path)}
          stats={stats}
          isLoading={cargandoStats}
        />,
      ];
    }

    const baseWidgets = [
      <WidgetBienvenida
        key="widget-bienvenida"
        nombre={nombreUsuario}
        rol={rolVisible}
        empresaNombre={empresaNombre}
      />,
    ];

    if (rolUsuario === "EMPLEADO") {
      baseWidgets.push(
        <WidgetResumenISO
          key="widget-resumen-iso"
          rol="EMPLEADO"
          stats={stats}
          isLoading={cargandoStats}
        />,
      );
      baseWidgets.push(
        <WidgetProgresoCursos
          key="widget-progreso-cursos"
          stats={stats}
          isLoading={cargandoStats}
          onAbrirCapacitacion={() => navigate('/dashboard/capacitacion')}
        />,
      );
      return baseWidgets;
    }

    if (rolUsuario === "LIDER_EQUIPO") {
      baseWidgets.push(
        <WidgetResumenISO
          key="widget-resumen-iso"
          rol="LIDER_EQUIPO"
          stats={stats}
          isLoading={cargandoStats}
          onExportarCumplimiento={() => navigate('/dashboard/reportes')}
        />,
      );
      return baseWidgets;
    }

    if (rolUsuario === "IMPLEMENTADOR") {
      baseWidgets.push(
        <WidgetResumenISO
          key="widget-resumen-iso"
          rol="IMPLEMENTADOR"
          stats={stats}
          isLoading={cargandoStats}
          onAbrirImplementacion={() => navigate('/dashboard/implementacion')}
        />,
      );
      return baseWidgets;
    }

    if (rolUsuario === "AUDITOR") {
      baseWidgets.push(
        <WidgetResumenISO
          key="widget-resumen-iso"
          rol="AUDITOR"
          stats={stats}
          isLoading={cargandoStats}
          onAbrirAuditorias={() => navigate('/dashboard/auditorias')}
        />,
      );
      return baseWidgets;
    }

    if (rolUsuario === "CAPACITADOR") {
      baseWidgets.push(
        <WidgetResumenISO
          key="widget-resumen-iso"
          rol="CAPACITADOR"
          stats={stats}
          isLoading={cargandoStats}
          onAbrirCapacitacion={() => navigate('/dashboard/capacitacion')}
        />,
      );
      baseWidgets.push(
        <WidgetProgresoCursos
          key="widget-progreso-cursos"
          stats={stats}
          isLoading={cargandoStats}
          onAbrirCapacitacion={() => navigate('/dashboard/capacitacion')}
        />,
      );
      return baseWidgets;
    }

    return baseWidgets;
  }, [cargandoStats, empresaNombre, esPerfilGlobal, esSuperAdmin, navigate, nombreUsuario, rolUsuario, rolVisible, stats]);

  return (
    <div className="space-y-8">
      <p className="sr-only" aria-live="polite">
        {isRefreshingStats ? 'Actualizando métricas del dashboard' : 'Métricas del dashboard actualizadas'}
      </p>

      {esPerfilGlobal ? (
        <div className="space-y-6">
          {widgets}
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {widgets}
        </div>
      )}

      {esAuditor && (
        <div className="bg-gradient-to-r from-blue-50 to-slate-50 border border-blue-200 rounded-xl p-5 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div>
              <div className="inline-flex items-center gap-2 text-blue-800 font-semibold">
                <BellRing className="w-5 h-5" />
                Centro de Notificaciones de Auditoría
              </div>
              <p className="text-sm text-slate-700 mt-1">
                {totalPendientes > 0
                  ? `Tienes ${totalPendientes} revisión(es) pendiente(s).`
                  : 'No tienes revisiones pendientes por ahora.'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/dashboard/auditorias')}
                className="px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold hover:bg-black"
              >
                Ir a Auditorías
              </button>
              {totalPendientes > 0 && (
                <button
                  onClick={marcarTodasLeidas}
                  disabled={actualizandoNotificacionId === -1}
                  className="px-4 py-2 rounded-lg bg-white border border-slate-300 text-slate-700 text-sm font-semibold hover:bg-slate-100 disabled:opacity-60"
                >
                  {actualizandoNotificacionId === -1 ? 'Marcando...' : 'Marcar todas'}
                </button>
              )}
            </div>
          </div>

          <div className="mt-4 space-y-2">
            {cargandoNotificaciones ? (
              <div className="inline-flex items-center gap-2 text-sm text-slate-600">
                <Loader2 className="w-4 h-4 animate-spin" />
                Cargando notificaciones...
              </div>
            ) : notificaciones.length === 0 ? (
              <div className="text-sm text-slate-500">Sin nuevas notificaciones in-app.</div>
            ) : (
              notificaciones.slice(0, 5).map((notificacion) => (
                <div
                  key={notificacion.id}
                  className="bg-white border border-slate-200 rounded-lg px-4 py-3 flex flex-col md:flex-row md:items-center md:justify-between gap-3"
                >
                  <div>
                    <p className="font-semibold text-slate-900">{notificacion.titulo}</p>
                    <p className="text-sm text-slate-700 mt-0.5">{notificacion.mensaje}</p>
                    <p className="text-xs text-slate-500 mt-1">
                      {new Date(notificacion.fecha_creacion).toLocaleString()}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      void marcarComoLeida(notificacion.id);
                    }}
                    disabled={actualizandoNotificacionId === notificacion.id}
                    className="inline-flex items-center gap-1 px-3 py-2 rounded-md border border-emerald-300 bg-emerald-50 text-emerald-700 text-xs font-semibold hover:bg-emerald-100 disabled:opacity-60"
                  >
                    <Check className="w-3.5 h-3.5" />
                    {actualizandoNotificacionId === notificacion.id ? 'Procesando...' : 'Marcar leída'}
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
