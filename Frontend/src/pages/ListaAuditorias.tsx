import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Calendar,
  Building2,
  CheckCircle2,
  Clock,
  TrendingUp,
  Loader2,
  Shield,
  XCircle,
  X,
  RotateCcw
} from "lucide-react";
import { apiFetch } from "../utils/api";

// ==================== INTERFACES ====================
interface ProcesoAuditoria {
  id: number;
  nombre: string;
  empresa: number;
  empresa_nombre: string;
  auditor: number;
  auditor_nombre: string;
  fecha_creacion: string;
  fecha_cierre: string | null;
  estado: "ACTIVA" | "FINALIZADA";
  visible_para_auditor: boolean;
  total_controles: number;
  controles_auditados: number;
  progreso_porcentaje: number;
  puede_finalizar: {
    puede: boolean;
    mensaje: string;
  };
}

interface FormularioCrear {
  nombre: string;
  empresa: number;
}

// ==================== COMPONENTE PRINCIPAL ====================
export function ListaAuditorias() {
  const navigate = useNavigate();
  
  // Obtener información del usuario
  const usuarioInfo = localStorage.getItem('usuario_info');
  const usuario = usuarioInfo ? JSON.parse(usuarioInfo) : null;
  const empresaId = usuario?.empresa_info?.id || null;

  // Estados
  const [procesos, setProcesos] = useState<ProcesoAuditoria[]>([]);
  const [cargando, setCargando] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [mostrarModal, setMostrarModal] = useState<boolean>(false);
  const [creando, setCreando] = useState<boolean>(false);
  const [archivandoIds, setArchivandoIds] = useState<number[]>([]);
  const [mostrarArchivadas, setMostrarArchivadas] = useState<boolean>(false);
  const [procesosArchivados, setProcesosArchivados] = useState<ProcesoAuditoria[]>([]);
  const [cargandoArchivadas, setCargandoArchivadas] = useState<boolean>(false);
  const [restaurandoIds, setRestaurandoIds] = useState<number[]>([]);
  
  const [formulario, setFormulario] = useState<FormularioCrear>({
    nombre: "",
    empresa: empresaId || 0
  });

  // ==================== CARGAR DATOS ====================
  useEffect(() => {
    cargarProcesos();
  }, []);

  const cargarProcesos = async () => {
    setCargando(true);
    setError("");
    
    try {
      const data = await apiFetch<ProcesoAuditoria[]>('/auditoria/procesos/');
      setProcesos(data);
    } catch (err: any) {
      console.error('Error al cargar procesos:', err);
      setError(err?.message || 'Error al cargar los programas de auditoría');
    } finally {
      setCargando(false);
    }
  };

  // ==================== CREAR PROCESO ====================
  const handleCrearProceso = async () => {
    if (!formulario.nombre.trim()) {
      alert('El nombre del proceso es obligatorio');
      return;
    }

    setCreando(true);

    try {
      const nuevoProceso = await apiFetch<ProcesoAuditoria>(
        '/auditoria/procesos/',
        {
          method: 'POST',
          body: JSON.stringify({
            nombre: formulario.nombre,
            empresa: formulario.empresa
          })
        }
      );
      
      // Redirigir a la vista de detalle
      navigate(`/dashboard/auditoria/proceso/${nuevoProceso.id}`);
      
    } catch (err: any) {
      console.error('Error al crear proceso:', err);
      alert(err?.message || 'Error al crear el proceso de auditoría');
    } finally {
      setCreando(false);
    }
  };

  const handleArchive = async (procesoId: number) => {
    const confirmar = window.confirm('¿Deseas ocultar esta auditoría de tu vista?');
    if (!confirmar) return;

    setArchivandoIds((prev) => [...prev, procesoId]);

    try {
      await apiFetch(`/auditoria/procesos/${procesoId}/archivar/`, {
        method: 'POST'
      });

      // Ocultar de inmediato en la vista sin eliminar en base de datos
      setProcesos((prev) => prev.filter((proceso) => proceso.id !== procesoId));
    } catch (err: any) {
      console.error('Error al archivar proceso:', err);
      alert(err?.message || 'No se pudo ocultar la auditoría. Intente nuevamente.');
    } finally {
      setArchivandoIds((prev) => prev.filter((id) => id !== procesoId));
    }
  };

  const cargarArchivadas = async () => {
    setCargandoArchivadas(true);

    try {
      const data = await apiFetch<ProcesoAuditoria[]>('/auditoria/procesos/archivados/');
      setProcesosArchivados(data);
    } catch (err: any) {
      console.error('Error al cargar auditorías archivadas:', err);
      alert(err?.message || 'No se pudieron cargar las auditorías archivadas.');
    } finally {
      setCargandoArchivadas(false);
    }
  };

  const abrirModalArchivadas = () => {
    setMostrarArchivadas(true);
    cargarArchivadas();
  };

  const handleRestaurar = async (procesoId: number) => {
    const confirmar = window.confirm('¿Deseas restaurar esta auditoría a tu vista principal?');
    if (!confirmar) return;

    setRestaurandoIds((prev) => [...prev, procesoId]);

    try {
      await apiFetch(`/auditoria/procesos/${procesoId}/restaurar/`, {
        method: 'POST'
      });

      // Quitar de archivadas y refrescar lista principal
      setProcesosArchivados((prev) => prev.filter((proceso) => proceso.id !== procesoId));
      await cargarProcesos();
    } catch (err: any) {
      console.error('Error al restaurar proceso:', err);
      alert(err?.message || 'No se pudo restaurar la auditoría. Intente nuevamente.');
    } finally {
      setRestaurandoIds((prev) => prev.filter((id) => id !== procesoId));
    }
  };

  // ==================== UTILIDADES ====================
  const getEstadoBadgeColor = (estado: string) => {
    return estado === "ACTIVA"
      ? "bg-blue-100 text-blue-800 border-blue-300"
      : "bg-gray-100 text-gray-800 border-gray-300";
  };

  const getEstadoIcon = (estado: string) => {
    return estado === "ACTIVA" ? (
      <Clock className="w-4 h-4" />
    ) : (
      <CheckCircle2 className="w-4 h-4" />
    );
  };

  const formatearFecha = (fecha: string) => {
    return new Date(fecha).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // ==================== RENDER: LOADING ====================
  if (cargando) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 font-medium">Cargando programas de auditoría...</p>
        </div>
      </div>
    );
  }

  // ==================== RENDER: ERROR ====================
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <XCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-red-900 font-bold text-lg">Error al cargar datos</h3>
            <p className="text-red-700 mt-1">{error}</p>
            <button
              onClick={cargarProcesos}
              className="mt-4 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors font-medium"
            >
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ==================== RENDER: VISTA PRINCIPAL ====================
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-800 to-blue-900 rounded-xl shadow-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Shield className="w-8 h-8" />
              <h1 className="text-3xl font-bold">Programas de Auditoría</h1>
            </div>
            <p className="text-blue-100 mt-1">
              Gestione procesos de auditoría ISO 27001 • Total: {procesos.length} programa(s)
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={abrirModalArchivadas}
              className="bg-white/15 text-white font-semibold py-3 px-4 rounded-lg hover:bg-white/25 transition-colors shadow-md flex items-center gap-2"
            >
              <RotateCcw className="w-5 h-5" />
              Restaurar Ocultas
            </button>

            <button
              onClick={() => setMostrarModal(true)}
              className="bg-yellow-400 text-black font-bold py-3 px-6 rounded-lg hover:bg-yellow-500 transition-colors shadow-md flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Nueva Auditoría
            </button>
          </div>
        </div>
      </div>

      {/* Grilla de Tarjetas */}
      {procesos.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-900 mb-2">No hay programas de auditoría</h3>
          <p className="text-gray-600 mb-6">Comience creando su primer proceso de auditoría</p>
          <button
            onClick={() => setMostrarModal(true)}
            className="bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Crear Primera Auditoría
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {procesos.map((proceso) => (
            <div
              key={proceso.id}
              onClick={() => navigate(`/dashboard/auditoria/proceso/${proceso.id}`)}
              className="bg-white rounded-xl shadow-md border border-gray-200 hover:border-blue-500 hover:shadow-xl transition-all cursor-pointer overflow-hidden group"
            >
              {/* Header de la Tarjeta */}
              <div className="bg-gradient-to-r from-slate-700 to-blue-800 p-4">
                <div className="flex items-start justify-between mb-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleArchive(proceso.id);
                    }}
                    disabled={archivandoIds.includes(proceso.id)}
                    className="mr-2 inline-flex items-center justify-center w-7 h-7 rounded-md bg-white/20 text-white hover:bg-white/30 transition-colors disabled:opacity-60"
                    title="Ocultar auditoría"
                    aria-label="Ocultar auditoría"
                  >
                    {archivandoIds.includes(proceso.id) ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <X className="w-4 h-4" />
                    )}
                  </button>
                  <h3 className="text-white font-bold text-lg line-clamp-2 flex-1">
                    {proceso.nombre}
                  </h3>
                  <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold border ml-2 ${getEstadoBadgeColor(proceso.estado)}`}>
                    {getEstadoIcon(proceso.estado)}
                    {proceso.estado === "ACTIVA" ? "Activa" : "Finalizada"}
                  </span>
                </div>
                
                <div className="flex items-center gap-2 text-blue-100 text-sm">
                  <Building2 className="w-4 h-4" />
                  <span className="font-medium">{proceso.empresa_nombre}</span>
                </div>
              </div>

              {/* Contenido de la Tarjeta */}
              <div className="p-5 space-y-4">
                {/* Auditor */}
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Shield className="w-4 h-4 text-gray-400" />
                  <span>Auditor: <span className="font-semibold text-gray-900">{proceso.auditor_nombre}</span></span>
                </div>

                {/* Fecha */}
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span>Creado: {formatearFecha(proceso.fecha_creacion)}</span>
                </div>

                {/* Progreso */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-gray-700 flex items-center gap-1">
                      <TrendingUp className="w-4 h-4 text-blue-600" />
                      Progreso
                    </span>
                    <span className="text-sm font-bold text-blue-600">
                      {proceso.progreso_porcentaje}%
                    </span>
                  </div>
                  
                  {/* Barra de Progreso */}
                  <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden shadow-inner">
                    <div
                      className={`h-3 rounded-full transition-all duration-500 ${
                        proceso.progreso_porcentaje === 100
                          ? 'bg-gradient-to-r from-green-500 to-green-600'
                          : 'bg-gradient-to-r from-blue-500 to-blue-600'
                      }`}
                      style={{ width: `${proceso.progreso_porcentaje}%` }}
                    />
                  </div>
                  
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>{proceso.controles_auditados} auditados</span>
                    <span>{proceso.total_controles} totales</span>
                  </div>
                </div>

                {/* Footer */}
                <div className="pt-3 border-t border-gray-200">
                  <button className="w-full bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors group-hover:bg-blue-700">
                    Ver Detalles →
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal de Auditorías Archivadas */}
      {mostrarArchivadas && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="bg-gradient-to-r from-slate-800 to-blue-900 text-white p-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  <RotateCcw className="w-6 h-6" />
                  Auditorías Ocultas
                </h2>
                <button
                  onClick={() => setMostrarArchivadas(false)}
                  className="text-white hover:text-gray-200 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {cargandoArchivadas ? (
                <div className="py-10 text-center">
                  <Loader2 className="w-10 h-10 text-blue-600 animate-spin mx-auto mb-3" />
                  <p className="text-gray-600">Cargando auditorías ocultas...</p>
                </div>
              ) : procesosArchivados.length === 0 ? (
                <div className="py-10 text-center">
                  <p className="text-gray-700 font-semibold">No hay auditorías ocultas para restaurar.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {procesosArchivados.map((proceso) => (
                    <div
                      key={proceso.id}
                      className="border border-gray-200 rounded-lg p-4 flex items-center justify-between gap-4"
                    >
                      <div>
                        <h3 className="font-bold text-gray-900">{proceso.nombre}</h3>
                        <p className="text-sm text-gray-600">{proceso.empresa_nombre}</p>
                        <p className="text-xs text-gray-500 mt-1">Ocultada en listado principal</p>
                      </div>

                      <button
                        onClick={() => handleRestaurar(proceso.id)}
                        disabled={restaurandoIds.includes(proceso.id)}
                        className="bg-green-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-60 flex items-center gap-2"
                      >
                        {restaurandoIds.includes(proceso.id) ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <RotateCcw className="w-4 h-4" />
                        )}
                        Restaurar
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal de Crear Proceso */}
      {mostrarModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
            {/* Header del Modal */}
            <div className="bg-gradient-to-r from-slate-800 to-blue-900 text-white p-6 rounded-t-xl">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  <Plus className="w-6 h-6" />
                  Nueva Auditoría
                </h2>
                <button
                  onClick={() => setMostrarModal(false)}
                  className="text-white hover:text-gray-200 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Contenido del Modal */}
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">
                  Nombre del Proceso de Auditoría *
                </label>
                <input
                  type="text"
                  value={formulario.nombre}
                  onChange={(e) => setFormulario({ ...formulario, nombre: e.target.value })}
                  placeholder="Ej: Auditoría Anual 2026, Auditoría de Recertificación Q1"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">
                  Empresa
                </label>
                <input
                  type="text"
                  value={usuario?.empresa_info?.nombre || 'Mi Empresa'}
                  disabled
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg bg-gray-100 text-gray-600"
                />
                <p className="text-xs text-gray-500 mt-1">
                  El proceso se creará para su empresa actual
                </p>
              </div>

              {/* Botones */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleCrearProceso}
                  disabled={creando || !formulario.nombre.trim()}
                  className="flex-1 bg-blue-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {creando ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Creando...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-5 h-5" />
                      Crear Proceso
                    </>
                  )}
                </button>
                <button
                  onClick={() => setMostrarModal(false)}
                  disabled={creando}
                  className="px-6 py-3 bg-gray-200 text-gray-700 font-bold rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
