import { useState, useEffect } from "react";
import { Save, CheckCircle, X, Paperclip } from "lucide-react";

interface ControlCardProps {
  control: {
    id: number;
    identificador: string;
    nombre: string;
    dominio: string;
    descripcion_guia: string;
  };
  empresaId: number;
  evaluacionPrevia?: {
    id: number;
    empresa: number;
    control: number;
    estado: string;
    justificacion: string;
    evidencia_url?: string;
    evidencia_nombre?: string;
  };
  onEvaluacionChange: () => void;
}

export function ControlCard({ control, empresaId, evaluacionPrevia, onEvaluacionChange }: ControlCardProps) {
  const usuarioInfo = localStorage.getItem('usuario_info');
  const usuario = usuarioInfo ? JSON.parse(usuarioInfo) : null;
  const puedeEditar = usuario?.rol === 'IMPLEMENTADOR';

  const [estadoSeleccionado, setEstadoSeleccionado] = useState<string>("");
  const [justificacion, setJustificacion] = useState<string>("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [evidenciaUrl, setEvidenciaUrl] = useState<string>("");
  const [evidenciaNombre, setEvidenciaNombre] = useState<string>("");
  const [guardado, setGuardado] = useState<boolean>(false);
  const [guardando, setGuardando] = useState<boolean>(false);
  const [evaluacionId, setEvaluacionId] = useState<number | null>(null);

  // Cargar datos de evaluación previa si existe
  useEffect(() => {
    if (evaluacionPrevia) {
      setEstadoSeleccionado(evaluacionPrevia.estado);
      setJustificacion(evaluacionPrevia.justificacion || "");
      setEvaluacionId(evaluacionPrevia.id);
      setEvidenciaUrl(evaluacionPrevia.evidencia_url || "");
      setEvidenciaNombre(evaluacionPrevia.evidencia_nombre || "");
      setGuardado(true);
    }
  }, [evaluacionPrevia]);

  const handleGuardar = async () => {
    if (!puedeEditar) {
      return;
    }

    if (!estadoSeleccionado) {
      alert("Debe seleccionar un estado");
      return;
    }

    // Validación condicional
    if (estadoSeleccionado === "NO_APLICA" && !justificacion.trim()) {
      alert("Debe proporcionar una justificación para 'No Aplica'");
      return;
    }

    setGuardando(true);

    try {
      // Crear FormData con todos los datos
      const formData = new FormData();
      formData.append('estado', estadoSeleccionado);
      formData.append('justificacion', justificacion);

      if (estadoSeleccionado !== "NO_APLICA" && archivo) {
        formData.append('evidencia', archivo);
      }

      // Obtener token de autenticación
      const token = localStorage.getItem('token_acceso');
      
      if (!token) {
        alert("No hay sesión activa. Por favor, inicie sesión nuevamente.");
        return;
      }

      const esActualizacion = Boolean(evaluacionId);
      const endpoint = esActualizacion
        ? `http://localhost:8000/api/implementacion/evaluaciones/${evaluacionId}/`
        : 'http://localhost:8000/api/implementacion/evaluaciones/';

      // Solo en creación se envían claves fijas (empresa/control).
      if (!esActualizacion) {
        formData.append('control', control.id.toString());
        formData.append('empresa', empresaId.toString());
      }

      // Realizar fetch autenticado
      const response = await fetch(endpoint, {
        method: esActualizacion ? 'PATCH' : 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
          // NO incluir Content-Type para que el navegador maneje el boundary de FormData
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al guardar la evaluación');
      }

      const data = await response.json();
      
      setEvaluacionId(data.id);
      
      // Guardar URL y nombre de evidencia si vienen del backend
      if (data.evidencia_url) {
        setEvidenciaUrl(data.evidencia_url);
      }
      if (data.evidencia_nombre) {
        setEvidenciaNombre(data.evidencia_nombre);
      }

      if (estadoSeleccionado === "NO_APLICA") {
        setArchivo(null);
        setEvidenciaUrl("");
        setEvidenciaNombre("");
      }
      
      setGuardado(true);
      
      // Notificar al componente padre para actualizar la lista
      onEvaluacionChange();
      
      alert(esActualizacion ? "Evaluación actualizada exitosamente" : "Evaluación guardada exitosamente");

    } catch (error: any) {
      console.error("Error al guardar evaluación:", error);
      alert(error.message || "Error al guardar la evaluación. Por favor, intente nuevamente.");
    } finally {
      setGuardando(false);
    }
  };

  const handleEditar = () => {
    if (!puedeEditar) {
      return;
    }

    setGuardado(false);
  };

  const handleCancelar = () => {
    // Reset local sin tocar API (sin DELETE).
    if (evaluacionPrevia) {
      setEstadoSeleccionado(evaluacionPrevia.estado);
      setJustificacion(evaluacionPrevia.justificacion || "");
      setEvidenciaUrl(evaluacionPrevia.evidencia_url || "");
      setEvidenciaNombre(evaluacionPrevia.evidencia_nombre || "");
      setEvaluacionId(evaluacionPrevia.id);
      setArchivo(null);
      setGuardado(true);
      return;
    }

    setEstadoSeleccionado("");
    setJustificacion("");
    setArchivo(null);
    setEvidenciaUrl("");
    setEvidenciaNombre("");
    setEvaluacionId(null);
    setGuardado(false);
  };

  const handleArchivoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setArchivo(file);
  };

  // Obtener URL del archivo para enlace
  const obtenerUrlArchivo = () => {
    if (evidenciaUrl) {
      return evidenciaUrl; // String del backend
    } else if (archivo) {
      return URL.createObjectURL(archivo); // File object recién subido
    }
    return null;
  };

  const obtenerNombreArchivo = () => {
    if (evidenciaNombre) {
      return evidenciaNombre;
    } else if (archivo) {
      return archivo.name;
    }
    return 'Evidencia adjunta';
  };

  // Mapeo de estados para mostrar
  const estadoTexto = {
    "IMPLEMENTADO": "Implementado",
    "EN_PROCESO": "En Proceso",
    "NO_APLICA": "No Aplica"
  };

  return (
    <div className="border border-gray-200 rounded-lg p-5 hover:border-yellow-400 transition-colors">
      {/* Header del Control */}
      <div className="mb-4">
        <div className="flex items-start gap-3 mb-2">
          <span className="text-xs font-bold text-white bg-yellow-500 px-3 py-1.5 rounded-md">
            {control.identificador}
          </span>
          <div className="flex-1">
            <h3 className="font-bold text-gray-900 text-lg">{control.nombre}</h3>
            <p className="text-xs text-gray-500 mt-1">
              Dominio: <span className="font-semibold">{control.dominio}</span>
            </p>
          </div>
          {guardado && (
            <div className="flex items-center gap-1 text-green-600 text-sm font-semibold">
              <CheckCircle className="w-5 h-5" />
              <span>Guardado</span>
            </div>
          )}
        </div>
        
        {/* Descripción siempre visible */}
        <p className="text-sm text-gray-600 mt-2 pl-1 bg-gray-50 p-3 rounded-lg">
          <span className="font-semibold text-gray-700">Descripción: </span>
          {control.descripcion_guia}
        </p>
      </div>

      {/* Vista de Resumen cuando está guardado */}
      {guardado ? (
        <div className="border-t border-gray-200 pt-4 space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="font-bold text-gray-900">
                  Estado: <span className="text-green-700">{estadoTexto[estadoSeleccionado as keyof typeof estadoTexto]} ✓</span>
                </span>
              </div>
              
              {justificacion && (
                <div className="mt-2">
                  <p className="text-sm font-semibold text-gray-700">Justificación:</p>
                  <p className="text-sm text-gray-600 mt-1 bg-white p-2 rounded border border-gray-200">
                    {justificacion}
                  </p>
                </div>
              )}

              {/* Evidencia adjunta */}
              {estadoSeleccionado !== "NO_APLICA" && (evidenciaUrl || archivo) && (
                <div className="mt-2">
                  <p className="text-sm font-semibold text-gray-700 mb-1">Evidencia:</p>
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <a
                      href={obtenerUrlArchivo() || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-2 text-sm"
                    >
                      <Paperclip className="w-4 h-4 flex-shrink-0" />
                      <span className="truncate">{obtenerNombreArchivo()}</span>
                    </a>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Botón Editar */}
          {puedeEditar ? (
            <div className="flex justify-end">
              <button
                onClick={handleEditar}
                className="flex items-center gap-2 bg-slate-600 text-white font-semibold py-2.5 px-5 rounded-lg hover:bg-slate-700 transition-colors shadow-sm"
              >
                <X className="w-4 h-4" />
                Editar Evaluación
              </button>
            </div>
          ) : (
            <div className="flex justify-end">
              <span className="text-xs font-semibold text-slate-600 bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-md">
                Modo solo lectura
              </span>
            </div>
          )}
        </div>
      ) : (
        /* Formulario de Evaluación cuando no está guardado */
        <div className="border-t border-gray-200 pt-4 space-y-4">
          {/* Estado */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Estado de Implementación *
            </label>
            <select
              value={estadoSeleccionado}
              onChange={(e) => setEstadoSeleccionado(e.target.value)}
              disabled={!puedeEditar}
              className="block w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none text-sm"
            >
              <option value="">Seleccionar...</option>
              <option value="IMPLEMENTADO">Implementado</option>
              <option value="EN_PROCESO">En Proceso</option>
              <option value="NO_APLICA">No Aplica</option>
            </select>
          </div>

          {/* Campos condicionales según el estado */}
          {estadoSeleccionado === "NO_APLICA" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Justificación *
              </label>
              <textarea
                value={justificacion}
                onChange={(e) => setJustificacion(e.target.value)}
                disabled={!puedeEditar}
                rows={3}
                placeholder="Explique por qué este control no aplica a su organización..."
                className="block w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none text-sm resize-none"
              />
            </div>
          )}

          {(estadoSeleccionado === "IMPLEMENTADO" || estadoSeleccionado === "EN_PROCESO") && (
            <>
              {/* Justificación */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {estadoSeleccionado === "EN_PROCESO" ? "Detalle de avance" : "Justificación"}
                </label>
                <textarea
                  value={justificacion}
                  onChange={(e) => setJustificacion(e.target.value)}
                  disabled={!puedeEditar}
                  rows={3}
                  placeholder={
                    estadoSeleccionado === "EN_PROCESO"
                      ? "Opcional: describe el avance actual de este control..."
                      : "Describa cómo se ha implementado este control..."
                  }
                  className="block w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none text-sm resize-none"
                />
              </div>

              {/* Evidencia */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {estadoSeleccionado === "EN_PROCESO" ? "Archivo de avance" : "Archivo de Evidencia"}
                </label>
                <input
                  type="file"
                  onChange={handleArchivoChange}
                  disabled={!puedeEditar}
                  className="block w-full text-sm text-gray-600 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-yellow-50 file:text-yellow-700 hover:file:bg-yellow-100 cursor-pointer border border-gray-300 rounded-lg"
                />
                {archivo && (
                  <p className="text-xs text-gray-500 mt-1">
                    Archivo seleccionado: {archivo.name}
                  </p>
                )}
              </div>
            </>
          )}

          {/* Botón Guardar */}
          {estadoSeleccionado && puedeEditar && (
            <div className="flex justify-end gap-2">
              <button
                onClick={handleCancelar}
                disabled={guardando}
                className="flex items-center gap-2 bg-gray-200 text-gray-800 font-semibold py-2.5 px-5 rounded-lg hover:bg-gray-300 transition-colors shadow-sm disabled:opacity-70"
              >
                <X className="w-4 h-4" />
                Cancelar
              </button>
              <button
                onClick={handleGuardar}
                disabled={guardando}
                className="flex items-center gap-2 bg-yellow-400 text-black font-semibold py-2.5 px-5 rounded-lg hover:bg-yellow-500 transition-colors shadow-sm disabled:opacity-70"
              >
                <Save className="w-4 h-4" />
                {guardando ? "Guardando..." : "Guardar Evaluación"}
              </button>
            </div>
          )}

          {!puedeEditar && (
            <div className="flex justify-end">
              <span className="text-xs font-semibold text-slate-600 bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-md">
                Solo IMPLEMENTADOR puede editar evaluaciones
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
