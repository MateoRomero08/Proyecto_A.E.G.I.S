import { useState, useEffect, useRef } from "react";
import { CheckCircle2, Trophy } from "lucide-react";
import confetti from "canvas-confetti";
import { toast } from "sonner";
import { apiFetch } from "../utils/api";
import { ControlCard } from "../components/ControlCard";

interface ControlAPI {
  id: number;
  identificador: string;
  nombre: string;
  dominio: string;
  descripcion_guia: string;
}

interface Evaluacion {
  id: number;
  empresa: number;
  control: number;
  estado: string;
  justificacion: string;
}

interface SolicitudRevisionResponse {
  detail: string;
  progreso: number;
  notificaciones_creadas: number;
  revision_solicitada: boolean;
  fecha_solicitud_revision: string | null;
}

interface EstadoSolicitudRevisionResponse {
  empresa_id: number;
  revision_solicitada: boolean;
  fecha_solicitud_revision: string | null;
}

const ESTADOS_COMPLETADOS = new Set(['IMPLEMENTADO', 'NO_APLICA']);

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

    return raw;
  } catch {
    return raw;
  }
};

export function ImplementacionISO() {
  // Leer información del usuario desde localStorage
  const usuarioInfo = localStorage.getItem('usuario_info');
  const usuario = usuarioInfo ? JSON.parse(usuarioInfo) : null;
  const empresaId = usuario?.empresa_info?.id || null;
  
  // Estados de controles y evaluaciones
  const [controlesAPI, setControlesAPI] = useState<ControlAPI[]>([]);
  const [evaluacionesPrevias, setEvaluacionesPrevias] = useState<Evaluacion[]>([]);
  const [cargando, setCargando] = useState(true);
  const [cargandoEvaluaciones, setCargandoEvaluaciones] = useState(false);
  const [mostrarAvisoCompletado, setMostrarAvisoCompletado] = useState(false);
  const [solicitandoRevision, setSolicitandoRevision] = useState(false);
  const [revisionSolicitada, setRevisionSolicitada] = useState(false);
  const [fechaSolicitudRevision, setFechaSolicitudRevision] = useState<string | null>(null);
  const yaCelebroRef = useRef(false);

  const dispararConfeti = () => {
    confetti({
      particleCount: 120,
      spread: 75,
      origin: { y: 0.65 }
    });

    window.setTimeout(() => {
      confetti({
        particleCount: 80,
        angle: 60,
        spread: 55,
        origin: { x: 0 }
      });
      confetti({
        particleCount: 80,
        angle: 120,
        spread: 55,
        origin: { x: 1 }
      });
    }, 220);
  };

  useEffect(() => {
    const cargarControles = async () => {
      try {
        const datos = await apiFetch<ControlAPI[]>('/implementacion/controles/');
        setControlesAPI(datos);
        setCargando(false);
      } catch (error) {
        console.error('Error al cargar los controles:', error);
        setCargando(false);
      }
    };

    cargarControles();
  }, []);

  useEffect(() => {
    if (empresaId) {
      cargarEvaluaciones(empresaId);
      cargarEstadoSolicitudRevision();
    }
  }, [empresaId]);

  const cargarEstadoSolicitudRevision = async () => {
    try {
      const estado = await apiFetch<EstadoSolicitudRevisionResponse>('/implementacion/evaluaciones/estado-solicitud-revision/');
      setRevisionSolicitada(Boolean(estado.revision_solicitada));
      setFechaSolicitudRevision(estado.fecha_solicitud_revision ?? null);
    } catch (error) {
      console.error('Error al cargar estado de solicitud de revision:', error);
    }
  };

  const cargarEvaluaciones = async (idEmpresa: number) => {
    setCargandoEvaluaciones(true);
    try {
      const datos = await apiFetch<Evaluacion[]>(`/implementacion/evaluaciones/?empresa=${idEmpresa}`);
      setEvaluacionesPrevias(datos);
    } catch (error) {
      console.error('Error al cargar evaluaciones:', error);
    } finally {
      setCargandoEvaluaciones(false);
    }
  };

  const handleEvaluacionChange = () => {
    if (empresaId) {
      cargarEvaluaciones(empresaId);
      cargarEstadoSolicitudRevision();
    }
  };

  const handleSolicitarRevision = async () => {
    if (solicitandoRevision || revisionSolicitada) {
      return;
    }

    setSolicitandoRevision(true);

    try {
      const response = await apiFetch<SolicitudRevisionResponse>('/implementacion/evaluaciones/solicitar-revision/', {
        method: 'POST',
      });

      setRevisionSolicitada(Boolean(response.revision_solicitada));
      setFechaSolicitudRevision(response.fecha_solicitud_revision ?? null);
      toast.success('Solicitud enviada a los auditores exitosamente', {
        description:
          response.notificaciones_creadas > 0
            ? `Se notificó a ${response.notificaciones_creadas} auditor(es) para iniciar la revisión.`
            : 'No se encontraron auditores activos en tu empresa. Contacta a tu líder de equipo.',
      });
    } catch (error) {
      toast.error('No se pudo enviar la solicitud de revisión', {
        description: parseApiError(error, 'Intenta nuevamente en unos segundos.'),
      });
    } finally {
      setSolicitandoRevision(false);
    }
  };

  // Calcular progreso
  const totalControles = controlesAPI.length;
  const controlesCompletados = evaluacionesPrevias.filter((evaluacion) => ESTADOS_COMPLETADOS.has(evaluacion.estado)).length;
  const progresoPorcentaje = totalControles > 0 ? Math.round((controlesCompletados / totalControles) * 100) : 0;
  const implementacionCompleta = totalControles > 0 && controlesCompletados === totalControles;

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

  return (
    <div className="space-y-6">
      {mostrarAvisoCompletado && (
        <div className="bg-green-50 border border-green-300 rounded-lg p-4 flex items-center gap-2 text-green-800">
          <CheckCircle2 className="w-5 h-5" />
          <span className="font-semibold">¡Implementación Completada! Has evaluado todos los controles.</span>
        </div>
      )}

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Implementación ISO 27001</h1>
        <p className="text-gray-600 mt-1">
          Empresa: <span className="font-semibold">{usuario?.empresa_info?.nombre || 'Mi Empresa'}</span>
        </p>
      </div>

      {/* Barra de Progreso */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-lg font-bold text-gray-900">Progreso de Implementación</h3>
            <p className="text-sm text-gray-600 mt-1">
              {controlesCompletados} de {totalControles} controles completados
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-3xl font-bold text-gray-900">{progresoPorcentaje}%</span>
          </div>
        </div>
        
        {/* Barra visual */}
        <div className="relative w-full h-6 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`absolute top-0 left-0 h-full transition-all duration-500 ${
              implementacionCompleta 
                ? 'bg-gradient-to-r from-green-500 to-green-600' 
                : 'bg-gradient-to-r from-yellow-400 to-yellow-500'
            }`}
            style={{ width: `${progresoPorcentaje}%` }}
          >
            {progresoPorcentaje > 10 && (
              <div className="flex items-center justify-center h-full">
                <span className="text-xs font-bold text-white">{progresoPorcentaje}%</span>
              </div>
            )}
          </div>
        </div>

        {/* Mensaje de completado */}
        {cargandoEvaluaciones && (
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-500">Actualizando progreso...</p>
          </div>
        )}
      </div>

      {/* Mensaje de Éxito 100% */}
      {implementacionCompleta && (
        <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-xl shadow-md border-2 border-green-500 p-8">
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="bg-green-500 rounded-full p-4">
              <Trophy className="w-12 h-12 text-white" />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-green-900 mb-2">
                ¡Implementación 100% Completada!
              </h2>
              <p className="text-green-700 text-lg">
                Ha evaluado exitosamente todos los {totalControles} controles de la ISO 27001:2022
              </p>
            </div>
            <button
              onClick={handleSolicitarRevision}
              disabled={solicitandoRevision || revisionSolicitada}
              className="bg-green-600 text-white font-bold py-4 px-8 rounded-lg hover:bg-green-700 transition-colors shadow-lg text-lg flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <CheckCircle2 className="w-6 h-6" />
              {solicitandoRevision
                ? 'Enviando solicitud...'
                : revisionSolicitada
                  ? 'Solicitud Enviada'
                  : 'Solicitar Revisión'}
            </button>

            {revisionSolicitada && (
              <div className="w-full max-w-2xl bg-white/70 border border-green-300 rounded-lg px-4 py-3 text-green-900 shadow-sm">
                <p className="font-semibold">Solicitud registrada correctamente</p>
                <p className="text-sm text-green-800 mt-1">
                  Tus auditores recibieron una notificación en su dashboard para iniciar la revisión pendiente.
                </p>
                {fechaSolicitudRevision && (
                  <p className="text-xs text-green-700 mt-2">
                    Enviada el {new Date(fechaSolicitudRevision).toLocaleString('es-CL')}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Lista de Controles */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-900">Controles ISO 27001:2022</h2>
          <p className="text-sm text-gray-600 mt-1">
            Usuario: <span className="font-semibold">{usuario?.username || 'Usuario'}</span> | Rol: <span className="font-semibold">{usuario?.rol || 'N/A'}</span>
          </p>
        </div>
        
        {cargando ? (
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400"></div>
            <span className="ml-3 text-gray-600">Cargando controles...</span>
          </div>
        ) : (
          <div className="space-y-4">
            {controlesAPI.map((control) => {
              const evaluacionPrevia = evaluacionesPrevias.find(e => e.control === control.id);
              return (
                <ControlCard 
                  key={control.id}
                  control={control}
                  empresaId={empresaId}
                  evaluacionPrevia={evaluacionPrevia}
                  onEvaluacionChange={handleEvaluacionChange}
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
