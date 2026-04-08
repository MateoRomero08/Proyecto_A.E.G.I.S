import { buildApiUrl } from './api';

const DASHBOARD_STATS_URL = buildApiUrl('/api/dashboard/stats/');

export type DashboardStatsScope = 'SUPERADMIN' | 'EMPRESA_ISO' | 'CAPACITACION';

export interface DashboardStatsResponse {
  scope: DashboardStatsScope;
  total_empresas?: number;
  total_usuarios?: number;
  total_cursos_globales?: number;
  porcentaje_cumplimiento_iso?: number;
  controles_pendientes?: number;
  cursos_activos?: number;
  controles_implementados?: number;
  controles_en_proceso?: number;
  total_controles?: number;
  mis_cursos_pendientes?: number;
  mis_modulos_completados?: number;
  total_modulos_activos?: number;
}

const buildHeaders = (): HeadersInit => {
  const token = localStorage.getItem('token_acceso');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
};

export const fetchDashboardStats = async (): Promise<DashboardStatsResponse> => {
  const response = await fetch(DASHBOARD_STATS_URL, {
    method: 'GET',
    headers: buildHeaders(),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Error HTTP ${response.status}`);
  }

  return response.json() as Promise<DashboardStatsResponse>;
};
