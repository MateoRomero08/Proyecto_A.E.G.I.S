const API_BASE = 'http://localhost:8000/api/reportes';

export interface EmpresaReporte {
  id: number;
  nombre: string;
  tipo: string;
}

export interface AuditoriaReporte {
  id: number;
  nombre: string;
  estado: string;
  fecha_creacion: string;
  fecha_cierre: string | null;
  auditor_nombre: string;
  empresa_nombre: string;
}

export interface PdfBlobPayload {
  blob: Blob;
  filename: string;
}

const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem('token_acceso');
  const headers: Record<string, string> = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
};

const extractFilename = (contentDisposition: string | null, fallback: string): string => {
  if (!contentDisposition) {
    return fallback;
  }

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }

  const normalMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
  if (normalMatch?.[1]) {
    return normalMatch[1];
  }

  return fallback;
};

export const descargarBlobComoArchivo = (blob: Blob, filename: string): void => {
  const url = URL.createObjectURL(blob);

  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
};

const fetchPdfBlob = async (endpoint: string, fallbackFilename: string): Promise<PdfBlobPayload> => {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Error HTTP ${response.status}`);
  }

  const blob = await response.blob();
  const filename = extractFilename(response.headers.get('content-disposition'), fallbackFilename);

  return { blob, filename };
};

const buildEmpresaQuery = (empresaId?: number | null): string => {
  if (!empresaId) {
    return '';
  }

  return `?empresa_id=${empresaId}`;
};

const fetchJson = async <T>(endpoint: string): Promise<T> => {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Error HTTP ${response.status}`);
  }

  return response.json() as Promise<T>;
};

export const listarEmpresasReportes = (): Promise<EmpresaReporte[]> => fetchJson<EmpresaReporte[]>('/empresas/');

export const listarAuditoriasReportes = (empresaId?: number | null): Promise<AuditoriaReporte[]> =>
  fetchJson<AuditoriaReporte[]>(`/auditorias/${buildEmpresaQuery(empresaId)}`);

export const obtenerReporteCumplimientoBlob = (empresaId?: number | null): Promise<PdfBlobPayload> =>
  fetchPdfBlob(`/cumplimiento/${buildEmpresaQuery(empresaId)}`, 'reporte-cumplimiento-iso.pdf');

export const obtenerReporteAuditoriaBlob = (idAuditoria: number, empresaId?: number | null): Promise<PdfBlobPayload> =>
  fetchPdfBlob(`/auditoria/${idAuditoria}/${buildEmpresaQuery(empresaId)}`, `reporte-auditoria-${idAuditoria}.pdf`);

export const obtenerReporteAccesosBlob = (empresaId?: number | null): Promise<PdfBlobPayload> =>
  fetchPdfBlob(`/accesos/${buildEmpresaQuery(empresaId)}`, 'reporte-matriz-accesos-a9.pdf');

export const obtenerReporteForenseBlob = (limit = 120): Promise<PdfBlobPayload> =>
  fetchPdfBlob(`/forense/?limit=${limit}`, 'reporte-forense-worm-aegis.pdf');

export const obtenerCertificadoCapacitacionBlob = (idProgreso: number): Promise<PdfBlobPayload> =>
  fetchPdfBlob(`/certificado/${idProgreso}/`, `certificado-${idProgreso}.pdf`);

export const descargarReporteCumplimiento = async (empresaId?: number | null): Promise<void> => {
  const data = await obtenerReporteCumplimientoBlob(empresaId);
  descargarBlobComoArchivo(data.blob, data.filename);
};

export const descargarReporteAuditoria = async (idAuditoria: number, empresaId?: number | null): Promise<void> => {
  const data = await obtenerReporteAuditoriaBlob(idAuditoria, empresaId);
  descargarBlobComoArchivo(data.blob, data.filename);
};

export const descargarReporteAccesos = async (empresaId?: number | null): Promise<void> => {
  const data = await obtenerReporteAccesosBlob(empresaId);
  descargarBlobComoArchivo(data.blob, data.filename);
};

export const descargarReporteForense = async (limit = 120): Promise<void> => {
  const data = await obtenerReporteForenseBlob(limit);
  descargarBlobComoArchivo(data.blob, data.filename);
};

export const descargarCertificadoCapacitacion = async (idProgreso: number): Promise<void> => {
  const data = await obtenerCertificadoCapacitacionBlob(idProgreso);
  descargarBlobComoArchivo(data.blob, data.filename);
};
