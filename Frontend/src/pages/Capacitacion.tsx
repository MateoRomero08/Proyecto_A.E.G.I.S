import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  BookOpen,
  Building2,
  CheckCircle2,
  Download,
  GraduationCap,
  Link2,
  Plus,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";

import {
  actualizarProgresoCurso,
  crearCursoCapacitacion,
  crearModuloContenido,
  eliminarCurso,
  eliminarModulo,
  CursoCapacitacion,
  listarCursosCapacitacion,
  TipoModulo,
} from "../utils/capacitacionApi";
import { esAdminSistema, esSuperusuario, obtenerUsuario } from "../utils/auth";
import {
  descargarBlobComoArchivo,
  obtenerCertificadoCapacitacionBlob,
} from "../utils/reportesApi";
import { PdfPreviewModal } from "../components/PdfPreviewModal";
import { usePermissions } from "../hooks/usePermissions";

type CursoFormState = {
  titulo: string;
  descripcion: string;
};

type ModuloFormState = {
  curso: string;
  titulo: string;
  descripcion: string;
  tipo: TipoModulo;
  url_recurso: string;
  orden: string;
  duracion_minutos: string;
};

const tiposModulo: Array<{ value: TipoModulo; label: string }> = [
  { value: 'VIDEO', label: 'Video' },
  { value: 'PDF', label: 'PDF / Lectura' },
  { value: 'CUESTIONARIO', label: 'Cuestionario' },
];

const parseApiError = (error: unknown, fallback: string): string => {
  if (!(error instanceof Error)) {
    return fallback;
  }

  const raw = error.message || fallback;
  const payload = raw.includes(' - ') ? raw.split(' - ').slice(1).join(' - ') : raw;

  try {
    const parsed = JSON.parse(payload);
    if (typeof parsed === 'string') return parsed;
    if (parsed?.detail) return String(parsed.detail);
    return raw;
  } catch {
    return raw;
  }
};

export function Capacitacion() {
  const usuario = obtenerUsuario();
  const esSuperAdmin = esSuperusuario();
  const esAdminGlobal = esAdminSistema();
  const esPerfilGlobal = esSuperAdmin || esAdminGlobal;
  const { hasPermission } = usePermissions(usuario);
  const empresaIdUsuario = usuario?.empresa_info?.id ?? null;

  const [cursos, setCursos] = useState<CursoCapacitacion[]>([]);
  const [cargandoCursos, setCargandoCursos] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const [mostrarPanelGestion, setMostrarPanelGestion] = useState(false);
  const [guardandoCurso, setGuardandoCurso] = useState(false);
  const [guardandoModulo, setGuardandoModulo] = useState(false);
  const [moduloAccionId, setModuloAccionId] = useState<number | null>(null);
  const [cursoEliminandoId, setCursoEliminandoId] = useState<number | null>(null);
  const [moduloEliminandoId, setModuloEliminandoId] = useState<number | null>(null);
  const [certificadoDescargandoId, setCertificadoDescargandoId] = useState<number | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewBlob, setPreviewBlob] = useState<Blob | null>(null);
  const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null);
  const [previewFileName, setPreviewFileName] = useState('certificado.pdf');
  const [previewTitle, setPreviewTitle] = useState('Previsualización de Certificado');

  const [cursoForm, setCursoForm] = useState<CursoFormState>({
    titulo: '',
    descripcion: '',
  });

  const [moduloForm, setModuloForm] = useState<ModuloFormState>({
    curso: '',
    titulo: '',
    descripcion: '',
    tipo: 'VIDEO',
    url_recurso: '',
    orden: '1',
    duracion_minutos: '10',
  });

  const puedeCrearCurso = esPerfilGlobal || hasPermission('capacitacion.add_curso');
  const puedeGestionar = esPerfilGlobal || hasPermission('capacitacion.change_curso');
  const puedeAbrirPanelGestion = puedeCrearCurso || puedeGestionar;
  const puedeReportarProgreso = !esPerfilGlobal && Boolean(empresaIdUsuario);

  const cargarCursos = async () => {
    setCargandoCursos(true);
    setErrorCarga(null);

    try {
      const data = await listarCursosCapacitacion();
      setCursos(data.filter((curso) => curso.activo));
    } catch (error) {
      const detalle = parseApiError(error, 'No se pudieron cargar los cursos de capacitacion.');
      setErrorCarga(detalle);
    } finally {
      setCargandoCursos(false);
    }
  };

  useEffect(() => {
    cargarCursos();
  }, []);

  const cursosGestionables = useMemo(() => {
    return cursos.filter((curso) => {
      if (esPerfilGlobal) {
        return curso.creado_por_admin;
      }

      if (puedeGestionar) {
        return !curso.creado_por_admin && curso.empresa === empresaIdUsuario;
      }

      return false;
    });
  }, [cursos, esPerfilGlobal, puedeGestionar, empresaIdUsuario]);

  useEffect(() => {
    if (cursosGestionables.length === 0) {
      setModuloForm((prev) => ({ ...prev, curso: '' }));
      return;
    }

    setModuloForm((prev) => {
      const cursoExiste = cursosGestionables.some((curso) => curso.id === Number(prev.curso));
      if (cursoExiste) {
        return prev;
      }

      return {
        ...prev,
        curso: String(cursosGestionables[0].id),
      };
    });
  }, [cursosGestionables]);

  const cursosCompletados = cursos.filter((curso) => curso.progreso.curso_completado).length;
  const progresoPromedio = cursos.length > 0
    ? Math.round(cursos.reduce((acc, curso) => acc + curso.progreso.porcentaje_completado, 0) / cursos.length)
    : 0;
  const modulosPendientes = cursos.reduce(
    (acc, curso) => acc + Math.max(curso.progreso.total_modulos - curso.progreso.modulos_completados_count, 0),
    0,
  );

  const tituloPanelGestion = esPerfilGlobal
    ? 'Panel Global: Catalogo Oficial Aegis'
    : 'Panel Gestion de Cursos Internos';

  const descripcionPanelGestion = esPerfilGlobal
    ? 'Los cursos creados aqui se publican para todas las empresas del SaaS.'
    : 'Gestiona cursos visibles solo para usuarios de tu empresa segun tus permisos.';

  const handleCrearCurso = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!cursoForm.titulo.trim()) {
      toast.error('El titulo del curso es obligatorio.');
      return;
    }

    setGuardandoCurso(true);
    try {
      await crearCursoCapacitacion({
        titulo: cursoForm.titulo.trim(),
        descripcion: cursoForm.descripcion.trim(),
      });

      setCursoForm({ titulo: '', descripcion: '' });
      toast.success('Curso creado correctamente.');
      await cargarCursos();
    } catch (error) {
      toast.error('No se pudo crear el curso.', {
        description: parseApiError(error, 'Intenta nuevamente en unos segundos.'),
      });
    } finally {
      setGuardandoCurso(false);
    }
  };

  const handleCrearModulo = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const cursoId = Number(moduloForm.curso);
    const orden = Number(moduloForm.orden);
    const duracion = Number(moduloForm.duracion_minutos);

    if (!cursoId) {
      toast.error('Selecciona un curso para el modulo.');
      return;
    }

    if (!moduloForm.titulo.trim() || !moduloForm.url_recurso.trim()) {
      toast.error('Titulo y URL del recurso son obligatorios.');
      return;
    }

    if (!Number.isFinite(orden) || orden <= 0 || !Number.isFinite(duracion) || duracion <= 0) {
      toast.error('Orden y duracion deben ser numeros positivos.');
      return;
    }

    setGuardandoModulo(true);
    try {
      await crearModuloContenido({
        curso: cursoId,
        titulo: moduloForm.titulo.trim(),
        descripcion: moduloForm.descripcion.trim(),
        tipo: moduloForm.tipo,
        url_recurso: moduloForm.url_recurso.trim(),
        orden,
        duracion_minutos: duracion,
      });

      setModuloForm((prev) => ({
        ...prev,
        titulo: '',
        descripcion: '',
        tipo: 'VIDEO',
        url_recurso: '',
        orden: String(orden + 1),
        duracion_minutos: '10',
      }));

      toast.success('Modulo agregado correctamente.');
      await cargarCursos();
    } catch (error) {
      toast.error('No se pudo crear el modulo.', {
        description: parseApiError(error, 'Revisa el formulario e intenta nuevamente.'),
      });
    } finally {
      setGuardandoModulo(false);
    }
  };

  const moduloCompletado = (curso: CursoCapacitacion, moduloId: number): boolean => {
    return curso.progreso.modulos_completados.includes(moduloId);
  };

  const puedeEliminarCurso = (curso: CursoCapacitacion): boolean => {
    if (!puedeGestionar) {
      return false;
    }

    if (curso.es_oficial_aegis) {
      return esPerfilGlobal;
    }

    if (esPerfilGlobal) {
      return false;
    }

    return curso.empresa === empresaIdUsuario;
  };

  const handleEliminarCurso = async (curso: CursoCapacitacion) => {
    const confirmado = window.confirm('¿Estás seguro de que deseas eliminar este elemento? Esta acción es irreversible.');
    if (!confirmado) {
      return;
    }

    setCursoEliminandoId(curso.id);
    try {
      await eliminarCurso(curso.id);

      setCursos((prev) => prev.filter((item) => item.id !== curso.id));
      setModuloForm((prev) => (
        Number(prev.curso) === curso.id
          ? { ...prev, curso: '' }
          : prev
      ));

      toast.success('Curso eliminado correctamente.');
    } catch (error) {
      toast.error('No se pudo eliminar el curso.', {
        description: parseApiError(error, 'No cuentas con permisos o el curso ya no existe.'),
      });
    } finally {
      setCursoEliminandoId(null);
    }
  };

  const handleEliminarModulo = async (curso: CursoCapacitacion, moduloId: number) => {
    const confirmado = window.confirm('¿Estás seguro de que deseas eliminar este elemento? Esta acción es irreversible.');
    if (!confirmado) {
      return;
    }

    setModuloEliminandoId(moduloId);
    try {
      await eliminarModulo(moduloId);

      setCursos((prev) => prev.map((item) => {
        if (item.id !== curso.id) {
          return item;
        }

        const modulosActualizados = item.modulos.filter((modulo) => modulo.id !== moduloId);
        const modulosCompletadosActualizados = item.progreso.modulos_completados.filter((id) => id !== moduloId);
        const totalModulos = modulosActualizados.length;
        const totalCompletados = modulosCompletadosActualizados.length;
        const porcentaje = totalModulos > 0 ? Math.round((totalCompletados / totalModulos) * 100) : 0;

        return {
          ...item,
          modulos: modulosActualizados,
          total_modulos: totalModulos,
          progreso: {
            ...item.progreso,
            modulos_completados: modulosCompletadosActualizados,
            modulos_completados_count: totalCompletados,
            total_modulos: totalModulos,
            porcentaje_completado: porcentaje,
            curso_completado: totalModulos > 0 && totalCompletados === totalModulos,
          },
        };
      }));

      toast.success('Modulo eliminado correctamente.');
    } catch (error) {
      toast.error('No se pudo eliminar el modulo.', {
        description: parseApiError(error, 'No cuentas con permisos o el modulo ya no existe.'),
      });
    } finally {
      setModuloEliminandoId(null);
    }
  };

  const handleToggleModulo = async (curso: CursoCapacitacion, moduloId: number, nuevoEstado: boolean) => {
    setModuloAccionId(moduloId);

    try {
      const response = await actualizarProgresoCurso(curso.id, {
        modulo_id: moduloId,
        completado: nuevoEstado,
      });

      setCursos((prev) => prev.map((item) => {
        if (item.id !== curso.id) {
          return item;
        }

        return {
          ...item,
          progreso: {
            porcentaje_completado: response.progreso.porcentaje_completado,
            curso_completado: response.progreso.curso_completado,
            modulos_completados: response.progreso.modulos_completados,
            modulos_completados_count: response.progreso.modulos_completados_count,
            total_modulos: response.progreso.total_modulos,
          },
        };
      }));

      toast.success(nuevoEstado ? 'Modulo marcado como completado.' : 'Modulo marcado como pendiente.');
    } catch (error) {
      toast.error('No se pudo actualizar el progreso.', {
        description: parseApiError(error, 'Intenta nuevamente.'),
      });
    } finally {
      setModuloAccionId(null);
    }
  };

  const handleDescargarCertificado = async (curso: CursoCapacitacion) => {
    const progresoId = curso.progreso.id;

    if (!progresoId) {
      toast.error('Este curso no tiene una traza de progreso valida para generar certificado.');
      return;
    }

    setCertificadoDescargandoId(progresoId);
    try {
      const data = await obtenerCertificadoCapacitacionBlob(progresoId);

      // Mobile-first: descarga directa por compatibilidad con visores PDF móviles.
      if (window.innerWidth < 768) {
        descargarBlobComoArchivo(data.blob, data.filename);
        toast.success(`Certificado de "${curso.titulo}" descargado.`);
        return;
      }

      if (previewBlobUrl) {
        URL.revokeObjectURL(previewBlobUrl);
      }

      const objectUrl = URL.createObjectURL(data.blob);
      setPreviewBlob(data.blob);
      setPreviewBlobUrl(objectUrl);
      setPreviewFileName(data.filename);
      setPreviewTitle(`Previsualización · Certificado ${curso.titulo}`);
      setPreviewOpen(true);

      toast.success(`Certificado de "${curso.titulo}" descargado.`);
    } catch (error) {
      toast.error('No se pudo descargar el certificado.', {
        description: parseApiError(error, 'Valida que el curso este finalizado al 100%.'),
      });
    } finally {
      setCertificadoDescargandoId(null);
    }
  };

  const cerrarPreviewCertificado = () => {
    setPreviewOpen(false);
    setPreviewBlob(null);
    if (previewBlobUrl) {
      URL.revokeObjectURL(previewBlobUrl);
    }
    setPreviewBlobUrl(null);
  };

  useEffect(() => {
    return () => {
      if (previewBlobUrl) {
        URL.revokeObjectURL(previewBlobUrl);
      }
    };
  }, [previewBlobUrl]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Capacitación</h1>
          <p className="text-gray-600 mt-1">
            Catalogo Oficial Aegis + Cursos internos de cada empresa en una sola experiencia de aprendizaje.
          </p>
        </div>

        {puedeAbrirPanelGestion && (
          <button
            onClick={() => setMostrarPanelGestion((prev) => !prev)}
            className="bg-yellow-400 text-black font-semibold py-3 px-5 rounded-lg hover:bg-yellow-500 transition-colors shadow-md flex items-center gap-2 w-fit"
          >
            <Plus className="w-5 h-5" />
            {mostrarPanelGestion ? 'Ocultar Gestion' : 'Gestionar Cursos'}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600">Cursos Completados</p>
            <CheckCircle2 className="w-5 h-5 text-green-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{cursosCompletados}/{cursos.length}</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600">Progreso Promedio</p>
            <BarChart3 className="w-5 h-5 text-yellow-600" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{progresoPromedio}%</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600">Modulos Pendientes</p>
            <BookOpen className="w-5 h-5 text-blue-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{modulosPendientes}</p>
        </div>
      </div>

      {puedeAbrirPanelGestion && mostrarPanelGestion && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{tituloPanelGestion}</h2>
            <p className="text-sm text-gray-600 mt-1">{descripcionPanelGestion}</p>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {puedeCrearCurso && (
              <form onSubmit={handleCrearCurso} className="border border-gray-200 rounded-lg p-4 space-y-3">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                  <GraduationCap className="w-5 h-5 text-yellow-600" />
                  Crear Curso
                </h3>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Titulo</label>
                  <input
                    type="text"
                    value={cursoForm.titulo}
                    onChange={(event) => setCursoForm((prev) => ({ ...prev, titulo: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none"
                    placeholder="Ej: Introduccion a ISO 27001"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Descripcion</label>
                  <textarea
                    value={cursoForm.descripcion}
                    onChange={(event) => setCursoForm((prev) => ({ ...prev, descripcion: event.target.value }))}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none resize-none"
                    placeholder="Resumen del objetivo del curso"
                  />
                </div>

                <button
                  type="submit"
                  disabled={guardandoCurso}
                  className="bg-yellow-400 text-black font-semibold py-2 px-5 rounded-lg hover:bg-yellow-500 transition-colors disabled:opacity-60"
                >
                  {guardandoCurso ? 'Guardando...' : 'Crear Curso'}
                </button>
              </form>
            )}

            {puedeGestionar && (
              <form onSubmit={handleCrearModulo} className="border border-gray-200 rounded-lg p-4 space-y-3">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                  <Link2 className="w-5 h-5 text-blue-600" />
                  Agregar Modulo de Contenido
                </h3>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Curso</label>
                <select
                  value={moduloForm.curso}
                  onChange={(event) => setModuloForm((prev) => ({ ...prev, curso: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none"
                  disabled={cursosGestionables.length === 0}
                >
                  {cursosGestionables.length === 0 ? (
                    <option value="">No hay cursos gestionables</option>
                  ) : (
                    cursosGestionables.map((curso) => (
                      <option key={curso.id} value={curso.id}>
                        {curso.titulo}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Titulo del modulo</label>
                <input
                  type="text"
                  value={moduloForm.titulo}
                  onChange={(event) => setModuloForm((prev) => ({ ...prev, titulo: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none"
                  placeholder="Ej: Video de apertura"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                  <select
                    value={moduloForm.tipo}
                    onChange={(event) => setModuloForm((prev) => ({ ...prev, tipo: event.target.value as TipoModulo }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none"
                  >
                    {tiposModulo.map((tipo) => (
                      <option key={tipo.value} value={tipo.value}>{tipo.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Orden</label>
                  <input
                    type="number"
                    min={1}
                    value={moduloForm.orden}
                    onChange={(event) => setModuloForm((prev) => ({ ...prev, orden: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">URL del recurso</label>
                <input
                  type="url"
                  value={moduloForm.url_recurso}
                  onChange={(event) => setModuloForm((prev) => ({ ...prev, url_recurso: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none"
                  placeholder="https://..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Duracion estimada (minutos)</label>
                <input
                  type="number"
                  min={1}
                  value={moduloForm.duracion_minutos}
                  onChange={(event) => setModuloForm((prev) => ({ ...prev, duracion_minutos: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descripcion del modulo</label>
                <textarea
                  rows={2}
                  value={moduloForm.descripcion}
                  onChange={(event) => setModuloForm((prev) => ({ ...prev, descripcion: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none resize-none"
                  placeholder="Contexto del contenido"
                />
              </div>

                <button
                  type="submit"
                  disabled={guardandoModulo || cursosGestionables.length === 0}
                  className="bg-blue-600 text-white font-semibold py-2 px-5 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-60"
                >
                  {guardandoModulo ? 'Guardando modulo...' : 'Agregar Modulo'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-2">Ruta de aprendizaje</h2>
        <p className="text-sm text-gray-600 mb-5">
          Los cursos con sello Oficial Aegis son globales. Los cursos Internos pertenecen solo a tu empresa.
        </p>

        {cargandoCursos ? (
          <div className="py-10 text-center text-gray-500">Cargando cursos...</div>
        ) : errorCarga ? (
          <div className="py-8 px-4 rounded-lg border border-red-200 bg-red-50 text-red-700">
            {errorCarga}
          </div>
        ) : cursos.length === 0 ? (
          <div className="py-10 text-center text-gray-500">
            No hay cursos disponibles para tu perfil.
          </div>
        ) : (
          <div className="space-y-5">
            {cursos.map((curso) => (
              <div key={curso.id} className="border border-gray-200 rounded-xl p-5 hover:border-yellow-400 transition-colors">
                <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-3 mb-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <h3 className="text-lg font-bold text-gray-900">{curso.titulo}</h3>

                      {curso.es_oficial_aegis ? (
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">
                          <ShieldCheck className="w-3.5 h-3.5" />
                          Oficial Aegis
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700">
                          <Building2 className="w-3.5 h-3.5" />
                          Interno Empresa
                        </span>
                      )}

                      {curso.progreso.curso_completado && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Finalizado
                        </span>
                      )}
                    </div>

                    <p className="text-sm text-gray-600">
                      {curso.descripcion || 'Este curso aun no tiene descripcion cargada.'}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200">
                      {curso.progreso.modulos_completados_count}/{curso.progreso.total_modulos} modulos completados
                    </div>

                    {!esPerfilGlobal && curso.progreso.curso_completado && curso.progreso.id && (
                      <button
                        onClick={() => {
                          void handleDescargarCertificado(curso);
                        }}
                        disabled={certificadoDescargandoId === curso.progreso.id}
                        className="inline-flex items-center gap-1 px-3 py-2 rounded-lg border border-emerald-300 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors disabled:opacity-60"
                        title="Descargar certificado de capacitación"
                      >
                        {certificadoDescargandoId === curso.progreso.id ? (
                          'Generando...'
                        ) : (
                          <>
                            <Download className="w-4 h-4" />
                            Certificado
                          </>
                        )}
                      </button>
                    )}

                    {mostrarPanelGestion && puedeGestionar && puedeEliminarCurso(curso) && (
                      <button
                        onClick={() => handleEliminarCurso(curso)}
                        disabled={cursoEliminandoId === curso.id}
                        className="inline-flex items-center gap-1 px-3 py-2 rounded-lg border border-red-300 bg-red-50 text-red-700 hover:bg-red-100 transition-colors disabled:opacity-60"
                        title="Eliminar curso"
                      >
                        <Trash2 className="w-4 h-4" />
                        {cursoEliminandoId === curso.id ? 'Eliminando...' : 'Eliminar'}
                      </button>
                    )}
                  </div>
                </div>

                <div className="mb-4">
                  <div className="flex items-center justify-between text-sm mb-1.5">
                    <span className="text-gray-600">Progreso del curso</span>
                    <span className="font-semibold text-gray-900">{curso.progreso.porcentaje_completado}%</span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-gray-200 overflow-hidden">
                    <div
                      className={`h-full transition-all ${curso.progreso.curso_completado ? 'bg-green-500' : 'bg-yellow-400'}`}
                      style={{ width: `${curso.progreso.porcentaje_completado}%` }}
                    />
                  </div>
                </div>

                {curso.modulos.length === 0 ? (
                  <div className="p-3 rounded-lg border border-gray-200 bg-gray-50 text-sm text-gray-600">
                    Este curso aun no tiene modulos publicados.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {curso.modulos.map((modulo) => {
                      const completado = moduloCompletado(curso, modulo.id);

                      return (
                        <div key={modulo.id} className="border border-gray-200 rounded-lg p-3.5 bg-white flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2 mb-1">
                              <span className="text-xs font-semibold px-2 py-1 rounded bg-gray-100 text-gray-700">
                                M{modulo.orden} · {modulo.tipo}
                              </span>
                              <p className="font-semibold text-gray-900">{modulo.titulo}</p>
                            </div>

                            <p className="text-sm text-gray-600 mb-1">
                              {modulo.descripcion || 'Sin descripcion adicional.'}
                            </p>

                            <a
                              href={modulo.url_recurso}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 hover:underline"
                            >
                              <Link2 className="w-4 h-4" />
                              Abrir recurso
                            </a>
                          </div>

                          <div className="flex items-center gap-2">
                            {puedeReportarProgreso && (
                              <button
                                onClick={() => handleToggleModulo(curso, modulo.id, !completado)}
                                disabled={moduloAccionId === modulo.id}
                                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors disabled:opacity-60 ${
                                  completado
                                    ? 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                                    : 'bg-yellow-400 text-black hover:bg-yellow-500'
                                }`}
                              >
                                {moduloAccionId === modulo.id
                                  ? 'Actualizando...'
                                  : completado
                                    ? 'Marcar Pendiente'
                                    : 'Marcar Completado'}
                              </button>
                            )}

                            {mostrarPanelGestion && puedeGestionar && puedeEliminarCurso(curso) && (
                              <button
                                onClick={() => handleEliminarModulo(curso, modulo.id)}
                                disabled={moduloEliminandoId === modulo.id}
                                className="inline-flex items-center gap-1 px-3 py-2 rounded-lg border border-red-300 bg-red-50 text-red-700 hover:bg-red-100 transition-colors disabled:opacity-60"
                                title="Eliminar modulo"
                              >
                                <Trash2 className="w-4 h-4" />
                                {moduloEliminandoId === modulo.id ? 'Eliminando...' : 'Eliminar'}
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <PdfPreviewModal
        isOpen={previewOpen}
        title={previewTitle}
        fileName={previewFileName}
        blobUrl={previewBlobUrl}
        onClose={cerrarPreviewCertificado}
        onDownload={() => {
          if (!previewBlob) {
            return;
          }
          descargarBlobComoArchivo(previewBlob, previewFileName);
        }}
      />
    </div>
  );
}
