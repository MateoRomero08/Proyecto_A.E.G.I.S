import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Search,
  FileText,
  CheckCircle,
  XCircle,
  AlertCircle,
  ClipboardCheck,
  Shield,
  Eye,
  X,
  Loader2,
  Filter,
  TrendingUp,
  Lock,
  ArrowLeft,
  Check,
  Pencil
} from "lucide-react";
import confetti from "canvas-confetti";
import { API_URL, apiFetch } from "../utils/api";

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
  total_controles: number;
  controles_auditados: number;
  progreso_porcentaje: number;
  puede_finalizar: {
    puede: boolean;
    mensaje: string;
  };
}

interface ControlISO {
  id: number;
  identificador: string;
  nombre: string;
  dominio: string;
  descripcion_guia: string;
}

interface EvaluacionControl {
  id: number;
  empresa: number;
  control: number;
  estado: "IMPLEMENTADO" | "EN_PROCESO" | "NO_IMPLEMENTADO" | "NO_APLICA";
  justificacion: string;
  evidencias?: Array<{
    id: number;
    archivo: string;
    fecha_subida: string;
  }>;
  evidencia_url?: string;
  evidencia_nombre?: string;
  nombre_implementador?: string;
}

interface RevisionAuditoria {
  id: number;
  proceso: number;
  proceso_estado: "ACTIVA" | "FINALIZADA";
  control_identificador: string;
  control_nombre: string;
  veredicto: "CONFORME" | "NO_CONFORME" | "NO_APLICA";
  observaciones: string;
  estado: "IMPLEMENTADO" | "EN_PROCESO" | "NO_IMPLEMENTADO" | "NO_APLICA" | "N/A" | null;
  justificacion: string | null;
  evidencia: string | null;
  // Campos dinámicos con lógica de snapshot
  estado_implementacion: "IMPLEMENTADO" | "EN_PROCESO" | "NO_IMPLEMENTADO" | "NO_APLICA";
  justificacion_implementacion: string;
  implementador_snapshot?: string | null;
  evidencias: Array<{
    id: number;
    archivo: string;
    archivo_nombre: string;
    fecha_subida: string;
  }>;
  // Metadata
  es_historico: boolean;
  fecha_revision: string;
  fecha_actualizacion: string;
}

interface ControlConEvaluacion {
  control: ControlISO;
  evaluacion: EvaluacionControl | null;
  revision?: RevisionAuditoria | null;
}

interface FormularioAuditoria {
  veredicto: "CONFORME" | "NO_CONFORME" | "NO_APLICA" | "";
  observaciones: string;
}

const BACKEND_MEDIA_ORIGIN = API_URL.replace(/\/$/, "");

const normalizarUrlArchivo = (url?: string | null): string | null => {
  if (!url) return null;

  const urlLimpia = url.trim();
  if (!urlLimpia) return null;

  if (urlLimpia.startsWith("http://") || urlLimpia.startsWith("https://")) {
    return urlLimpia;
  }

  if (urlLimpia.startsWith("/")) {
    return `${BACKEND_MEDIA_ORIGIN}${urlLimpia}`;
  }

  return `${BACKEND_MEDIA_ORIGIN}/${urlLimpia}`;
};

const obtenerNombreArchivoDesdeUrl = (url: string): string => {
  const sinQuery = url.split("?")[0].replace(/\/$/, "");
  const nombre = sinQuery.split("/").pop();

  if (!nombre) {
    return "Evidencia adjunta";
  }

  try {
    return decodeURIComponent(nombre);
  } catch {
    return nombre;
  }
};

// ==================== COMPONENTE PRINCIPAL ====================
export function Auditoria() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const procesoId = id ? parseInt(id) : null;

  // Estados de datos
  const [proceso, setProceso] = useState<ProcesoAuditoria | null>(null);
  const [controlesConEvaluacion, setControlesConEvaluacion] = useState<ControlConEvaluacion[]>([]);

  // Estados de UI
  const [cargando, setCargando] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [busqueda, setBusqueda] = useState<string>("");
  const [filtroEstado, setFiltroEstado] = useState<string>("TODOS");
  const [finalizando, setFinalizando] = useState<boolean>(false);

  // Estados del panel de auditoría
  const [controlSeleccionado, setControlSeleccionado] = useState<ControlConEvaluacion | null>(null);
  const [formulario, setFormulario] = useState<FormularioAuditoria>({
    veredicto: "",
    observaciones: ""
  });
  const [enviando, setEnviando] = useState<boolean>(false);
  const [mostrarAvisoCompletado, setMostrarAvisoCompletado] = useState<boolean>(false);
  const yaCelebroRef = useRef<boolean>(false);

  const dispararConfeti = () => {
    confetti({
      particleCount: 110,
      spread: 70,
      origin: { y: 0.65 }
    });

    window.setTimeout(() => {
      confetti({
        particleCount: 70,
        angle: 60,
        spread: 55,
        origin: { x: 0 }
      });
      confetti({
        particleCount: 70,
        angle: 120,
        spread: 55,
        origin: { x: 1 }
      });
    }, 220);
  };

  // ==================== CARGAR DATOS ====================
  useEffect(() => {
    if (procesoId) {
      cargarDatos(true);
    }
  }, [procesoId]);

  const cargarDatos = async (showLoader: boolean = true) => {
    if (!procesoId) return;

    if (showLoader) {
      setCargando(true);
    }
    setError("");

    try {
      // Cargar primero el proceso para obtener la empresa correcta
      const procesoData = await apiFetch<ProcesoAuditoria>(`/auditoria/procesos/${procesoId}/`);

      // Cargar controles, evaluaciones y revisiones del proceso en paralelo
      const [controlesData, evaluacionesData, revisionesData] = await Promise.all([
        apiFetch<ControlISO[]>('/implementacion/controles/'),
        apiFetch<EvaluacionControl[]>(`/implementacion/evaluaciones/?empresa=${procesoData.empresa}`),
        apiFetch<RevisionAuditoria[]>(`/auditoria/revisiones/?proceso=${procesoId}`)
      ]);

      setProceso(procesoData);

      const revisionesPorControl = new Map<string, RevisionAuditoria>(
        revisionesData.map((revision) => [revision.control_identificador, revision])
      );

      // Combinar controles con sus evaluaciones
      const combinados: ControlConEvaluacion[] = controlesData.map(control => {
        const evaluacion = evaluacionesData.find(ev => ev.control === control.id) || null;
        const revision = revisionesPorControl.get(control.identificador) || null;
        return { control, evaluacion, revision };
      });

      setControlesConEvaluacion(combinados);

    } catch (err: any) {
      console.error('Error al cargar datos:', err);
      const mensajeError = err?.message || 'Error al cargar los datos de auditoría';
      setError(mensajeError);
    } finally {
      if (showLoader) {
        setCargando(false);
      }
    }
  };

  // ==================== FINALIZAR PROCESO ====================
  const handleFinalizarProceso = async () => {
    if (!procesoId || !proceso) return;

    const confirmar = window.confirm(
      `¿Está seguro de finalizar el proceso "${proceso.nombre}"?\n\n` +
      'Una vez finalizado, no se podrán realizar más cambios en las revisiones.\n' +
      'Esta acción es irreversible.'
    );

    if (!confirmar) return;

    setFinalizando(true);

    try {
      await apiFetch(`/auditoria/procesos/${procesoId}/finalizar/`, {
        method: 'POST'
      });

      alert('Proceso de auditoría finalizado exitosamente');
      
      // Recargar datos para actualizar el estado
      await cargarDatos(false);

    } catch (err: any) {
      console.error('Error al finalizar proceso:', err);
      alert(err?.message || 'Error al finalizar el proceso de auditoría');
    } finally {
      setFinalizando(false);
    }
  };

  // ==================== LÓGICA DE AUDITORÍA ====================
  const handleSeleccionarControl = (item: ControlConEvaluacion) => {
    setControlSeleccionado(item);
    setFormulario({
      veredicto: item.revision?.veredicto || "",
      observaciones: item.revision?.observaciones || ""
    });
  };

  const handleCerrarPanel = () => {
    setControlSeleccionado(null);
    setFormulario({
      veredicto: "",
      observaciones: ""
    });
  };

  const handleEnviarAuditoria = async () => {
    if (!controlSeleccionado?.evaluacion || !procesoId) {
      alert("No hay evaluación para auditar");
      return;
    }

    if (!formulario.veredicto) {
      alert("Debe seleccionar un veredicto");
      return;
    }

    setEnviando(true);

    try {
      const esEdicion = Boolean(controlSeleccionado?.revision);

      await apiFetch(
        `/auditoria/revisiones/`,
        {
          method: 'POST',
          body: JSON.stringify({
            proceso: procesoId,
            evaluacion_control: controlSeleccionado.evaluacion.id,
            veredicto: formulario.veredicto,
            observaciones: formulario.observaciones
          })
        }
      );
      alert(esEdicion ? 'Auditoría actualizada exitosamente' : 'Auditoría registrada exitosamente');

      // Cerrar panel
      handleCerrarPanel();
      
      // Recargar datos para actualizar el progreso
      await cargarDatos(false);

    } catch (err: any) {
      console.error('Error al enviar auditoría:', err);
      const mensajeError = err?.message || 'Error al registrar la auditoría';
      alert(mensajeError);
    } finally {
      setEnviando(false);
    }
  };

  const progresoPorcentaje = proceso?.progreso_porcentaje ?? 0;

  useEffect(() => {
    if (progresoPorcentaje === 100 && !yaCelebroRef.current) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      dispararConfeti();
      setMostrarAvisoCompletado(true);
      yaCelebroRef.current = true;
    }

    if (progresoPorcentaje < 100) {
      setMostrarAvisoCompletado(false);
      yaCelebroRef.current = false;
    }
  }, [progresoPorcentaje]);

  useEffect(() => {
    if (!mostrarAvisoCompletado) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setMostrarAvisoCompletado(false);
    }, 5000);

    return () => window.clearTimeout(timeoutId);
  }, [mostrarAvisoCompletado]);

  // ==================== FILTRADO ====================
  const controlesFilterados = controlesConEvaluacion.filter(item => {
    const cumpleBusqueda =
      item.control.identificador.toLowerCase().includes(busqueda.toLowerCase()) ||
      item.control.nombre.toLowerCase().includes(busqueda.toLowerCase());

    const estadoEvaluacion = item.evaluacion?.estado;

    const cumpleEstado =
      filtroEstado === "TODOS" ||
      (filtroEstado === "IMPLEMENTADO" && estadoEvaluacion === "IMPLEMENTADO") ||
      (filtroEstado === "EN_PROCESO" && estadoEvaluacion === "EN_PROCESO") ||
      (filtroEstado === "NO_IMPLEMENTADO" && estadoEvaluacion === "NO_IMPLEMENTADO") ||
      (filtroEstado === "NO_APLICA" && estadoEvaluacion === "NO_APLICA") ||
      (filtroEstado === "SIN_EVALUAR" && !item.evaluacion);

    return cumpleBusqueda && cumpleEstado;
  });

  // ==================== UTILIDADES UI ====================
  const getEstadoColor = (estado: string | undefined) => {
    switch (estado) {
      case "IMPLEMENTADO":
        return "bg-green-100 text-green-800 border-green-300";
      case "EN_PROCESO":
        return "bg-amber-100 text-amber-700 border-amber-300";
      case "NO_IMPLEMENTADO":
        return "bg-red-100 text-red-800 border-red-300";
      case "NO_APLICA":
        return "bg-sky-100 text-sky-800 border-sky-300";
      default:
        return "bg-gray-100 text-gray-600 border-gray-300";
    }
  };

  const getEstadoTexto = (estado: string | undefined) => {
    switch (estado) {
      case "IMPLEMENTADO":
        return "Implementado";
      case "EN_PROCESO":
        return "En Proceso";
      case "NO_IMPLEMENTADO":
        return "No Implementado";
      case "NO_APLICA":
        return "No Aplica";
      default:
        return "Sin Evaluar";
    }
  };

  const getEstadoIcon = (estado: string | undefined) => {
    switch (estado) {
      case "IMPLEMENTADO":
        return <CheckCircle className="w-4 h-4" />;
      case "EN_PROCESO":
        return <TrendingUp className="w-4 h-4" />;
      case "NO_IMPLEMENTADO":
        return <XCircle className="w-4 h-4" />;
      case "NO_APLICA":
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  // ==================== RENDER: ESTADO DE CARGA ====================
  if (cargando) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 font-medium">Cargando proceso de auditoría...</p>
        </div>
      </div>
    );
  }

  // ==================== RENDER: ESTADO DE ERROR ====================
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <XCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-red-900 font-bold text-lg">Error al cargar datos</h3>
            <p className="text-red-700 mt-1">{error}</p>
            <button
              onClick={() => cargarDatos(true)}
              className="mt-4 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors font-medium"
            >
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!proceso) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <p className="text-yellow-800">Proceso no encontrado</p>
      </div>
    );
  }

  const estaFinalizada = proceso.estado === 'FINALIZADA';
  const isReadOnly = estaFinalizada;
  const puedeFinalizarse = proceso.progreso_porcentaje === 100 && proceso.estado === 'ACTIVA';
  const modoEdicion = Boolean(controlSeleccionado?.revision);
  const estadoModal = controlSeleccionado?.revision?.estado ?? controlSeleccionado?.revision?.estado_implementacion;
  const justificacionModal = controlSeleccionado?.revision?.justificacion ?? controlSeleccionado?.revision?.justificacion_implementacion;
  const evidenciasModal = controlSeleccionado?.revision?.evidencias ?? [];
  const evidenciaModal = controlSeleccionado?.revision?.evidencia;
  const estadoImplementacionDetalle = (modoEdicion ? estadoModal : controlSeleccionado?.evaluacion?.estado) ?? undefined;
  const esEnProcesoDetalle = estadoImplementacionDetalle === 'EN_PROCESO';
  const evidenciasImplementacionDetalle = (controlSeleccionado?.evaluacion?.evidencias ?? [])
    .map((evidencia) => ({
      ...evidencia,
      archivo_normalizado: normalizarUrlArchivo(evidencia.archivo)
    }))
    .filter((evidencia): evidencia is { id: number; archivo: string; fecha_subida: string; archivo_normalizado: string } =>
      Boolean(evidencia.archivo_normalizado)
    );
  const evidenciaImplementacionPrincipal = normalizarUrlArchivo(controlSeleccionado?.evaluacion?.evidencia_url);

  // ==================== RENDER: VISTA PRINCIPAL ====================
  return (
    <div className="space-y-6">
      {mostrarAvisoCompletado && (
        <div className="bg-green-50 border border-green-300 rounded-lg p-4 flex items-center gap-2 text-green-800">
          <CheckCircle className="w-5 h-5" />
          <span className="font-semibold">¡Auditoría Completada! Ya puedes finalizar el proceso</span>
        </div>
      )}

      {/* Header del Proceso */}
      <div className="bg-gradient-to-r from-slate-800 to-blue-900 rounded-xl shadow-lg p-6 text-white">
        <div className="flex items-center gap-3 mb-4">
          <button
            onClick={() => navigate('/dashboard/auditorias')}
            className="text-white hover:text-blue-200 transition-colors"
          >
            <ArrowLeft className="w-6 h-6" />
          </button>
          <Shield className="w-8 h-8" />
          <div className="flex-1">
            <h1 className="text-3xl font-bold">{proceso.nombre}</h1>
            <p className="text-blue-100 mt-1">
              Empresa: {proceso.empresa_nombre} • Auditor: {proceso.auditor_nombre}
            </p>
          </div>

          {/* Estado del Proceso */}
          <div className="flex items-center gap-3">
            {estaFinalizada ? (
              <div className="bg-gray-700 px-4 py-2 rounded-lg flex items-center gap-2">
                <Lock className="w-5 h-5" />
                <span className="font-bold">FINALIZADA</span>
              </div>
            ) : (
              <div className="bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2">
                <ClipboardCheck className="w-5 h-5" />
                <span className="font-bold">ACTIVA</span>
              </div>
            )}
          </div>
        </div>

        {/* Barra de Progreso */}
        <div className="bg-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-bold flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Progreso de Auditoría
            </span>
            <span className="text-2xl font-bold">{proceso.progreso_porcentaje}%</span>
          </div>

          <div className="w-full bg-white/20 rounded-full h-4 overflow-hidden">
            <div
              className={`h-4 rounded-full transition-all duration-500 ${
                proceso.progreso_porcentaje === 100
                  ? 'bg-gradient-to-r from-green-400 to-green-500'
                  : 'bg-gradient-to-r from-yellow-400 to-yellow-500'
              }`}
              style={{ width: `${proceso.progreso_porcentaje}%` }}
            />
          </div>

          <div className="flex justify-between text-sm text-blue-100 mt-2">
            <span>{proceso.controles_auditados} controles auditados</span>
            <span>{proceso.total_controles} controles totales</span>
          </div>
        </div>

        {/* Botón Finalizar */}
        {puedeFinalizarse && (
          <div className="mt-4">
            <button
              onClick={handleFinalizarProceso}
              disabled={finalizando}
              className="w-full bg-green-500 text-white font-bold py-3 px-6 rounded-lg hover:bg-green-600 transition-colors shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {finalizando ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Finalizando...
                </>
              ) : (
                <>
                  <Check className="w-5 h-5" />
                  Finalizar Auditoría
                </>
              )}
            </button>
          </div>
        )}

        {/* Mensaje de Solo Lectura */}
        {estaFinalizada && (
          <div className="mt-4 space-y-2">
            <div className="bg-gray-700 rounded-lg p-3 flex items-center gap-2 text-sm">
              <Lock className="w-4 h-4" />
              <span>Esta auditoría está finalizada y es de solo lectura</span>
            </div>
            <div className="bg-purple-700 rounded-lg p-3 text-sm">
              <div className="flex items-center gap-2 mb-1">
                <Lock className="w-4 h-4" />
                <span className="font-bold">Datos Históricos Congelados</span>
              </div>
              <p className="text-xs text-purple-100">
                Los datos mostrados son una fotografía exacta del momento de cierre. 
                Aunque los controles hayan cambiado posteriormente, esta auditoría permanece inmutable.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Filtros y Búsqueda */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              placeholder="Buscar por código o nombre del control..."
            />
          </div>

          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <select
              value={filtroEstado}
              onChange={(e) => setFiltroEstado(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none appearance-none bg-white cursor-pointer"
            >
              <option value="TODOS">Todos los estados</option>
              <option value="IMPLEMENTADO">Implementados</option>
              <option value="EN_PROCESO">En Proceso</option>
              <option value="NO_IMPLEMENTADO">No Implementados</option>
              <option value="NO_APLICA">No Aplica</option>
              <option value="SIN_EVALUAR">Sin Evaluar</option>
            </select>
          </div>
        </div>

        <div className="mt-3 text-sm text-gray-600">
          Mostrando <span className="font-semibold text-gray-900">{controlesFilterados.length}</span> de {controlesConEvaluacion.length} controles
        </div>
      </div>

      {/* Tabla de Controles */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px]">
            <thead className="bg-slate-700 text-white">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Código</th>
                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Control</th>
                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Dominio</th>
                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Estado</th>
                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Evidencia</th>
                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {controlesFilterados.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600 font-medium">No se encontraron controles</p>
                  </td>
                </tr>
              ) : (
                controlesFilterados.map((item) => {
                  const estadoTabla = item.revision
                    ? item.revision.estado
                    : item.evaluacion?.estado;
                  const evidenciaRevisionTabla = item.revision
                    ? normalizarUrlArchivo(item.revision.evidencia)
                    : null;
                  const evidenciaEvaluacionTabla = normalizarUrlArchivo(
                    item.evaluacion?.evidencia_url
                      ?? item.evaluacion?.evidencias?.[0]?.archivo
                      ?? null
                  );
                  const evidenciaTabla = item.revision
                    ? evidenciaRevisionTabla
                    : evidenciaEvaluacionTabla;
                  const totalEvidenciasEvaluacion = item.evaluacion?.evidencias?.length || 0;

                  return (
                    <tr
                      key={item.control.id}
                      className="hover:bg-blue-50 transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-3 py-1.5 rounded-lg bg-blue-600 text-white font-bold text-sm">
                          {item.control.identificador}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-gray-900">{item.control.nombre}</div>
                        <div className="text-sm text-gray-500 mt-1 line-clamp-1">
                          {item.control.descripcion_guia}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-700 font-medium">
                          {item.control.dominio}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border ${getEstadoColor(estadoTabla ?? undefined)}`}>
                          {getEstadoIcon(estadoTabla ?? undefined)}
                          {getEstadoTexto(estadoTabla ?? undefined)}
                        </span>
                        {!item.revision && item.evaluacion?.nombre_implementador && (
                          <div className="text-xs text-gray-500 mt-1">
                            Por: {item.evaluacion.nombre_implementador}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {evidenciaTabla ? (
                          <a
                            href={evidenciaTabla}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium text-sm transition-colors"
                          >
                            <Eye className="w-4 h-4" />
                            {!item.revision && totalEvidenciasEvaluacion > 1
                              ? `Ver Evidencias (${totalEvidenciasEvaluacion})`
                              : 'Ver Evidencia'}
                          </a>
                        ) : (
                          <span className="text-gray-400 text-sm">Sin evidencia</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {!estaFinalizada ? (
                          item.revision ? (
                            <div className="flex items-center gap-2">
                              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 text-xs font-bold">
                                <Check className="w-3.5 h-3.5" />
                                Auditado
                              </span>
                              <button
                                onClick={() => handleSeleccionarControl(item)}
                                className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors border border-slate-300"
                                title="Editar auditoría"
                                aria-label="Editar auditoría"
                              >
                                <Pencil className="w-4 h-4" />
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => handleSeleccionarControl(item)}
                              className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
                            >
                              <ClipboardCheck className="w-4 h-4" />
                              Auditar
                            </button>
                          )
                        ) : (
                          <button
                            onClick={() => handleSeleccionarControl(item)}
                            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-300 bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors font-medium text-sm"
                            title="Ver detalle de auditoría"
                            aria-label="Ver detalle de auditoría"
                          >
                            <Eye className="w-4 h-4" />
                            Ver Detalle
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Panel Lateral de Auditoría */}
      {controlSeleccionado && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-end">
          <div className="bg-white h-full w-full md:w-[600px] shadow-2xl overflow-y-auto">
            {/* Header del Panel */}
            <div className="sticky top-0 bg-gradient-to-r from-slate-800 to-blue-900 text-white p-6 shadow-lg">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  <ClipboardCheck className="w-7 h-7" />
                  {isReadOnly ? 'Detalle de Auditoría' : (modoEdicion ? 'Editar Auditoría' : 'Realizar Auditoría')}
                </h2>
                <button
                  onClick={handleCerrarPanel}
                  className="text-white hover:text-gray-200 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              <div className="flex items-center gap-2 text-blue-100">
                <span className="bg-blue-700 px-3 py-1 rounded-md font-bold text-sm">
                  {controlSeleccionado.control.identificador}
                </span>
                <span className="text-sm">{controlSeleccionado.control.nombre}</span>
              </div>
            </div>

            {/* Contenido del Panel */}
            <div className="p-6 space-y-6">
              {/* Información del Control */}
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <h3 className="font-bold text-slate-900 mb-2 flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Descripción del Control
                </h3>
                <p className="text-sm text-slate-700 leading-relaxed">
                  {controlSeleccionado.control.descripcion_guia}
                </p>
                <div className="mt-3 pt-3 border-t border-slate-300">
                  <span className="text-xs font-semibold text-slate-600">Dominio: </span>
                  <span className="text-sm text-slate-900 font-medium">
                    {controlSeleccionado.control.dominio}
                  </span>
                </div>
              </div>

              {/* Estado de Implementación */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-bold text-blue-900">Estado de Implementación</h3>
                  {controlSeleccionado.revision?.es_historico && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 text-xs font-bold rounded-full border border-purple-300">
                      <Lock className="w-3 h-3" />
                      SNAPSHOT
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-bold border ${
                    getEstadoColor(estadoImplementacionDetalle)
                  }`}>
                    {getEstadoIcon(estadoImplementacionDetalle)}
                    {getEstadoTexto(estadoImplementacionDetalle)}
                  </span>
                </div>
                {modoEdicion && (
                  <p className="text-sm text-slate-500 font-medium mt-2">
                    Implementado por: {controlSeleccionado.revision?.implementador_snapshot || 'Sin asignar'}
                  </p>
                )}
                {controlSeleccionado.revision?.es_historico && (
                  <p className="text-xs text-purple-600 font-medium mt-2 italic">
                    📸 Estado congelado al momento de finalizar la auditoría
                  </p>
                )}
                {!modoEdicion && controlSeleccionado.evaluacion?.nombre_implementador && (
                  <p className="text-sm text-slate-500 font-medium mt-2">
                    Implementado por: {controlSeleccionado.evaluacion.nombre_implementador}
                  </p>
                )}
                {((modoEdicion && justificacionModal) || (!modoEdicion && controlSeleccionado.evaluacion?.justificacion)) && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-blue-700 mb-1">
                      {esEnProcesoDetalle ? 'Justificación de avance:' : 'Justificación:'}
                    </p>
                    <p className="text-sm text-blue-900 bg-white p-3 rounded border border-blue-200">
                      {modoEdicion ? justificacionModal : controlSeleccionado.evaluacion?.justificacion}
                    </p>
                    {controlSeleccionado.revision?.es_historico && (
                      <p className="text-xs text-purple-600 font-medium mt-1 italic">
                        ℹ️ Justificación del momento de la auditoría
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Evidencia */}
              {((modoEdicion && (evidenciasModal.length > 0 || Boolean(evidenciaModal))) ||
                (!modoEdicion && (evidenciasImplementacionDetalle.length > 0 || Boolean(evidenciaImplementacionPrincipal)))) && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-bold text-green-900">
                      {esEnProcesoDetalle ? 'Evidencia Parcial' : 'Evidencia Adjunta'}
                    </h3>
                    {controlSeleccionado.revision?.es_historico && (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 text-xs font-bold rounded-full border border-purple-300">
                        <Lock className="w-3 h-3" />
                        SNAPSHOT
                      </span>
                    )}
                  </div>
                  
                  {/* Evidencias de la revisión (snapshot) */}
                  {modoEdicion ? (
                    evidenciasModal.length > 0 ? (
                      <div className="space-y-2">
                        {evidenciasModal.map((evidencia, index) => (
                          <a
                            key={index}
                            href={evidencia.archivo}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block p-2 bg-white border border-green-300 rounded hover:bg-green-100 transition-colors"
                          >
                            <div className="flex items-center gap-2 text-green-700 hover:text-green-900 font-medium">
                              <Eye className="w-5 h-5" />
                              <span>{evidencia.archivo_nombre}</span>
                            </div>
                            <p className="text-xs text-slate-500 ml-7">
                              Subido: {new Date(evidencia.fecha_subida).toLocaleDateString()}
                            </p>
                          </a>
                        ))}
                        {controlSeleccionado.revision?.es_historico && (
                          <p className="text-xs text-purple-600 font-medium mt-2 italic">
                            ✅ Evidencias congeladas del momento de la auditoría
                          </p>
                        )}
                      </div>
                    ) : (
                      evidenciaModal && (
                        <a
                          href={evidenciaModal}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 text-green-700 hover:text-green-900 font-medium underline"
                        >
                          <Eye className="w-5 h-5" />
                          Ver evidencia de la revisión
                        </a>
                      )
                    )
                  ) : (
                    evidenciasImplementacionDetalle.length > 0 ? (
                      <div className="space-y-2">
                        {evidenciasImplementacionDetalle.map((evidencia) => (
                          <a
                            key={evidencia.id}
                            href={evidencia.archivo_normalizado}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block p-2 bg-white border border-green-300 rounded hover:bg-green-100 transition-colors"
                          >
                            <div className="flex items-center gap-2 text-green-700 hover:text-green-900 font-medium">
                              <Eye className="w-5 h-5" />
                              <span>{obtenerNombreArchivoDesdeUrl(evidencia.archivo_normalizado)}</span>
                            </div>
                            <p className="text-xs text-slate-500 ml-7">
                              Subido: {new Date(evidencia.fecha_subida).toLocaleDateString()}
                            </p>
                          </a>
                        ))}
                      </div>
                    ) : (
                      evidenciaImplementacionPrincipal && (
                        <a
                          href={evidenciaImplementacionPrincipal}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 text-green-700 hover:text-green-900 font-medium underline"
                        >
                          <Eye className="w-5 h-5" />
                          {controlSeleccionado.evaluacion?.evidencia_nombre || obtenerNombreArchivoDesdeUrl(evidenciaImplementacionPrincipal)}
                        </a>
                      )
                    )
                  )}
                </div>
              )}

              {/* Formulario de Auditoría */}
              <div className="bg-white border-2 border-blue-600 rounded-lg p-5">
                <h3 className="font-bold text-slate-900 mb-4 text-lg">Veredicto de Auditoría</h3>

                {/* Veredicto */}
                <div className="mb-4">
                  <label className="block text-sm font-bold text-slate-700 mb-2">
                    Veredicto *
                  </label>
                  <select
                    value={formulario.veredicto}
                    onChange={(e) => setFormulario({ ...formulario, veredicto: e.target.value as "CONFORME" | "NO_CONFORME" | "NO_APLICA" | "" })}
                    disabled={isReadOnly}
                    className="w-full px-4 py-3 border-2 border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm font-medium"
                  >
                    <option value="">Seleccione un veredicto...</option>
                    <option value="CONFORME">✓ CONFORME - Control cumple con los requisitos</option>
                    <option value="NO_CONFORME">✗ NO CONFORME - Control no cumple</option>
                    <option value="NO_APLICA">− NO APLICA - Control no aplica al contexto</option>
                  </select>
                </div>

                {/* Observaciones */}
                <div className="mb-5">
                  <label className="block text-sm font-bold text-slate-700 mb-2">
                    Observaciones del Auditor
                  </label>
                  <textarea
                    value={formulario.observaciones}
                    onChange={(e) => setFormulario({ ...formulario, observaciones: e.target.value })}
                    disabled={isReadOnly}
                    rows={5}
                    placeholder="Ingrese hallazgos, recomendaciones o comentarios sobre la auditoría..."
                    className="w-full px-4 py-3 border-2 border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm resize-none"
                  />
                </div>

                {/* Botones de Acción */}
                <div className="flex gap-3">
                  {!isReadOnly && (
                    <button
                      onClick={handleEnviarAuditoria}
                      disabled={enviando || !formulario.veredicto}
                      className="flex-1 bg-blue-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {enviando ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          {modoEdicion ? 'Actualizando...' : 'Registrando...'}
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-5 h-5" />
                          {modoEdicion ? 'Actualizar Auditoría' : 'Registrar Auditoría'}
                        </>
                      )}
                    </button>
                  )}
                  <button
                    onClick={handleCerrarPanel}
                    disabled={enviando}
                    className="px-6 py-3 bg-gray-200 text-gray-700 font-bold rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50"
                  >
                    {isReadOnly ? 'Cerrar' : 'Cancelar'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
