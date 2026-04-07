import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Building2,
  ClipboardList,
  Download,
  FileLock2,
  FileText,
  Loader2,
  Shield,
} from "lucide-react";
import { toast } from "sonner";

import {
  descargarBlobComoArchivo,
  listarAuditoriasReportes,
  listarEmpresasReportes,
  obtenerReporteAccesosBlob,
  obtenerReporteAuditoriaBlob,
  obtenerReporteCumplimientoBlob,
  obtenerReporteForenseBlob,
  type PdfBlobPayload,
  type AuditoriaReporte,
  type EmpresaReporte,
} from "../utils/reportesApi";
import { esSuperusuario, obtenerRolUsuario, obtenerUsuario } from "../utils/auth";
import { PdfPreviewModal } from "../components/PdfPreviewModal";

const parseApiError = (error: unknown, fallback: string): string => {
  if (!(error instanceof Error)) {
    return fallback;
  }

  const raw = error.message || fallback;
  const payload = raw.includes(' - ') ? raw.split(' - ').slice(1).join(' - ') : raw;

  try {
    const parsed = JSON.parse(payload);
    if (typeof parsed === 'string') {
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

export function Reportes() {
  const usuario = obtenerUsuario();
  const esSuperAdmin = esSuperusuario();
  const rol = obtenerRolUsuario();
  const esLider = rol === 'LIDER_EQUIPO';

  const [empresas, setEmpresas] = useState<EmpresaReporte[]>([]);
  const [empresaSeleccionadaId, setEmpresaSeleccionadaId] = useState<number | null>(null);
  const [auditorias, setAuditorias] = useState<AuditoriaReporte[]>([]);
  const [cargandoEmpresas, setCargandoEmpresas] = useState(false);
  const [cargandoAuditorias, setCargandoAuditorias] = useState(false);
  const [accionDescarga, setAccionDescarga] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewBlob, setPreviewBlob] = useState<Blob | null>(null);
  const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null);
  const [previewFileName, setPreviewFileName] = useState('reporte.pdf');
  const [previewTitle, setPreviewTitle] = useState('Previsualización PDF');

  const accesoPermitido = esSuperAdmin || esLider;

  useEffect(() => {
    if (!accesoPermitido) {
      return;
    }

    let mounted = true;

    const cargarEmpresas = async () => {
      setCargandoEmpresas(true);
      try {
        const data = await listarEmpresasReportes();
        if (!mounted) {
          return;
        }

        setEmpresas(data);

        if (esSuperAdmin) {
          setEmpresaSeleccionadaId((prev) => prev ?? data[0]?.id ?? null);
        } else {
          const empresaPropia = data[0]?.id ?? usuario?.empresa_info?.id ?? null;
          setEmpresaSeleccionadaId(empresaPropia);
        }
      } catch (error) {
        if (mounted) {
          toast.error('No se pudieron cargar las empresas para reportes.', {
            description: parseApiError(error, 'Intenta nuevamente en unos segundos.'),
          });
        }
      } finally {
        if (mounted) {
          setCargandoEmpresas(false);
        }
      }
    };

    void cargarEmpresas();

    return () => {
      mounted = false;
    };
  }, [accesoPermitido, esSuperAdmin, usuario?.empresa_info?.id]);

  useEffect(() => {
    if (!accesoPermitido) {
      return;
    }

    if (esSuperAdmin && !empresaSeleccionadaId) {
      setAuditorias([]);
      return;
    }

    let mounted = true;

    const cargarAuditorias = async () => {
      setCargandoAuditorias(true);
      try {
        const data = await listarAuditoriasReportes(esSuperAdmin ? empresaSeleccionadaId : null);
        if (mounted) {
          setAuditorias(data);
        }
      } catch (error) {
        if (mounted) {
          toast.error('No se pudo cargar el listado de auditorias.', {
            description: parseApiError(error, 'Intenta nuevamente.'),
          });
        }
      } finally {
        if (mounted) {
          setCargandoAuditorias(false);
        }
      }
    };

    void cargarAuditorias();

    return () => {
      mounted = false;
    };
  }, [accesoPermitido, empresaSeleccionadaId, esSuperAdmin]);

  const empresaSeleccionada = useMemo(
    () => empresas.find((empresa) => empresa.id === empresaSeleccionadaId) || null,
    [empresas, empresaSeleccionadaId],
  );

  const cerrarPreview = () => {
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

  const ejecutarExportacionPDF = async (
    accionKey: string,
    callback: () => Promise<PdfBlobPayload>,
    successMessage: string,
    previewHeading: string,
  ) => {
    setAccionDescarga(accionKey);
    try {
      const data = await callback();

      // Mobile-first: descarga directa para evitar limitaciones de visor PDF en navegadores móviles.
      if (window.innerWidth < 768) {
        descargarBlobComoArchivo(data.blob, data.filename);
        toast.success(successMessage);
        return;
      }

      if (previewBlobUrl) {
        URL.revokeObjectURL(previewBlobUrl);
      }

      const objectUrl = URL.createObjectURL(data.blob);
      setPreviewBlob(data.blob);
      setPreviewBlobUrl(objectUrl);
      setPreviewFileName(data.filename);
      setPreviewTitle(previewHeading);
      setPreviewOpen(true);

      toast.success(successMessage);
    } catch (error) {
      toast.error('No se pudo descargar el reporte.', {
        description: parseApiError(error, 'Valida permisos y disponibilidad de datos.'),
      });
    } finally {
      setAccionDescarga(null);
    }
  };

  if (!accesoPermitido) {
    return (
      <div className="bg-white rounded-xl border border-red-200 p-6 text-red-700">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 mt-0.5" />
          <div>
            <h1 className="text-xl font-bold">Acceso restringido</h1>
            <p className="text-sm mt-1">Este modulo de reportes solo esta habilitado para SuperAdmin y Lider de Equipo.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white p-6 shadow-md">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-yellow-300 font-semibold">Centro de Reportes</p>
            <h1 className="text-3xl font-black mt-1">Exportacion Profesional ISO 27001</h1>
            <p className="text-sm text-slate-200 mt-2 max-w-3xl">
              Genera documentos PDF oficiales de cumplimiento, auditoria y control de accesos.
              {esSuperAdmin
                ? ' Como SuperAdmin puedes operar reportes por tenant y emitir el extracto forense WORM global.'
                : ' Como Lider de Equipo, la exportacion se limita automaticamente a tu empresa.'}
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 min-w-[280px]">
            <div className="rounded-xl bg-white/10 border border-white/20 p-3">
              <p className="text-xs text-slate-300 uppercase">Empresa activa</p>
              <p className="text-lg font-bold text-white mt-1">{empresaSeleccionada?.nombre || usuario?.empresa_info?.nombre || 'Sin empresa'}</p>
            </div>
            <div className="rounded-xl bg-white/10 border border-white/20 p-3">
              <p className="text-xs text-slate-300 uppercase">Auditorias detectadas</p>
              <p className="text-lg font-bold text-white mt-1">{cargandoAuditorias ? '...' : auditorias.length}</p>
            </div>
          </div>
        </div>
      </section>

      {esSuperAdmin && (
        <section className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3 text-slate-800 font-semibold">
            <Building2 className="w-4 h-4" />
            Seleccion de Tenant
          </div>

          <div className="max-w-md">
            <label htmlFor="empresa-reportes" className="block text-sm text-gray-600 mb-1">Empresa objetivo</label>
            <select
              id="empresa-reportes"
              value={empresaSeleccionadaId ?? ''}
              onChange={(event) => setEmpresaSeleccionadaId(Number(event.target.value) || null)}
              disabled={cargandoEmpresas}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none"
            >
              {empresas.length === 0 ? (
                <option value="">No hay empresas disponibles</option>
              ) : (
                empresas.map((empresa) => (
                  <option key={empresa.id} value={empresa.id}>
                    {empresa.nombre} ({empresa.tipo})
                  </option>
                ))
              )}
            </select>
          </div>
        </section>
      )}

      <section className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <article className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-lg font-bold text-gray-900">Reportes de Cumplimiento y Accesos</h2>
          <p className="text-sm text-gray-600 mt-1">Documentos ejecutivos listos para auditoria externa y comites internos.</p>

          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              onClick={() => {
                void ejecutarExportacionPDF(
                  'cumplimiento',
                  () => obtenerReporteCumplimientoBlob(esSuperAdmin ? empresaSeleccionadaId : null),
                  'Reporte de estado de cumplimiento exportado.',
                  'Previsualización · Estado de Cumplimiento ISO',
                );
              }}
              disabled={accionDescarga === 'cumplimiento' || (esSuperAdmin && !empresaSeleccionadaId)}
              className="inline-flex items-center justify-center gap-2 bg-yellow-400 text-black font-semibold py-2.5 px-4 rounded-lg hover:bg-yellow-500 transition-colors disabled:opacity-60"
            >
              {accionDescarga === 'cumplimiento' ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
              Exportar Estado ISO
            </button>

            <button
              onClick={() => {
                void ejecutarExportacionPDF(
                  'accesos',
                  () => obtenerReporteAccesosBlob(esSuperAdmin ? empresaSeleccionadaId : null),
                  'Matriz de accesos exportada.',
                  'Previsualización · Matriz de Accesos (A.9)',
                );
              }}
              disabled={accionDescarga === 'accesos' || (esSuperAdmin && !empresaSeleccionadaId)}
              className="inline-flex items-center justify-center gap-2 bg-slate-900 text-white font-semibold py-2.5 px-4 rounded-lg hover:bg-black transition-colors disabled:opacity-60"
            >
              {accionDescarga === 'accesos' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              Exportar Matriz de Accesos
            </button>
          </div>
        </article>

        <article className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-lg font-bold text-gray-900">Reporte Forense AEGIS</h2>
          <p className="text-sm text-gray-600 mt-1">Extracto WORM de eventos criticos de seguridad del SaaS.</p>

          {esSuperAdmin ? (
            <button
              onClick={() => {
                void ejecutarExportacionPDF(
                  'forense',
                  () => obtenerReporteForenseBlob(120),
                  'Reporte forense WORM exportado.',
                  'Previsualización · Reporte Forense WORM',
                );
              }}
              disabled={accionDescarga === 'forense'}
              className="mt-4 inline-flex items-center justify-center gap-2 bg-red-700 text-white font-semibold py-2.5 px-4 rounded-lg hover:bg-red-800 transition-colors disabled:opacity-60"
            >
              {accionDescarga === 'forense' ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileLock2 className="w-4 h-4" />}
              Exportar Bitacora WORM (Aegis Global)
            </button>
          ) : (
            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 text-amber-700 px-4 py-3 text-sm">
              El reporte forense WORM es exclusivo de SuperAdmin.
            </div>
          )}
        </article>
      </section>

      <section className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="px-5 py-4 border-b border-gray-200 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Auditorias Disponibles para Exportar</h2>
            <p className="text-sm text-gray-600">Descarga individual de procesos de auditoria por tenant.</p>
          </div>

          <div className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border border-slate-200 bg-slate-50 text-slate-700">
            <ClipboardList className="w-3.5 h-3.5" />
            {cargandoAuditorias ? 'Actualizando...' : `${auditorias.length} proceso(s)`}
          </div>
        </div>

        <div className="p-5">
          {cargandoAuditorias ? (
            <div className="text-sm text-gray-500 inline-flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Cargando auditorias...
            </div>
          ) : auditorias.length === 0 ? (
            <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-gray-600">
              No existen auditorias disponibles para la empresa seleccionada.
            </div>
          ) : (
            <div className="space-y-3">
              {auditorias.map((auditoria) => {
                const accionKey = `auditoria-${auditoria.id}`;

                return (
                  <div
                    key={auditoria.id}
                    className="rounded-lg border border-gray-200 p-4 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3"
                  >
                    <div>
                      <p className="font-semibold text-gray-900">{auditoria.nombre}</p>
                      <p className="text-sm text-gray-600 mt-0.5">
                        Estado: <span className="font-semibold">{auditoria.estado}</span> · Auditor: {auditoria.auditor_nombre}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Creada: {new Date(auditoria.fecha_creacion).toLocaleDateString()} · Empresa: {auditoria.empresa_nombre}
                      </p>
                    </div>

                    <button
                      onClick={() => {
                        void ejecutarExportacionPDF(
                          accionKey,
                          () => obtenerReporteAuditoriaBlob(auditoria.id, esSuperAdmin ? empresaSeleccionadaId : null),
                          `Reporte de auditoria "${auditoria.nombre}" exportado.`,
                          `Previsualización · Auditoría ${auditoria.nombre}`,
                        );
                      }}
                      disabled={accionDescarga === accionKey}
                      className="inline-flex items-center justify-center gap-2 bg-white border border-slate-300 text-slate-700 font-semibold py-2 px-4 rounded-lg hover:bg-slate-100 transition-colors disabled:opacity-60"
                    >
                      {accionDescarga === accionKey ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                      Descargar PDF
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      <section className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800 flex items-start gap-2">
        <Shield className="w-4 h-4 mt-0.5" />
        Todos los reportes exportados son generados en tiempo real y respetan aislamiento multi-tenant, trazabilidad y RBAC.
      </section>

      <PdfPreviewModal
        isOpen={previewOpen}
        title={previewTitle}
        fileName={previewFileName}
        blobUrl={previewBlobUrl}
        onClose={cerrarPreview}
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
