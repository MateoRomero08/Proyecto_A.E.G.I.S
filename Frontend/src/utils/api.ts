// src/utils/api.ts

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_ORIGIN = API_URL.replace(/\/$/, '');

const normalizeOrigin = (value: string): string | null => {
  try {
    return new URL(value).origin;
  } catch {
    return null;
  }
};

const buildAllowedApiOrigins = (): Set<string> => {
  const origins = new Set<string>();
  const baseOrigin = normalizeOrigin(API_ORIGIN) ?? normalizeOrigin(API_URL);

  if (baseOrigin) {
    origins.add(baseOrigin);
  }

  const extraOriginsRaw = String(import.meta.env.VITE_API_ALLOWED_ORIGINS || '');
  extraOriginsRaw
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean)
    .forEach((origin) => {
      const normalized = normalizeOrigin(origin);
      if (normalized) {
        origins.add(normalized);
      }
    });

  if (!baseOrigin && typeof window !== 'undefined' && window.location?.origin) {
    origins.add(window.location.origin);
  }

  return origins;
};

const ALLOWED_API_ORIGINS = buildAllowedApiOrigins();

const isAllowedApiUrl = (value: string): boolean => {
  try {
    const parsed = new URL(value);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return false;
    }
    return ALLOWED_API_ORIGINS.has(parsed.origin);
  } catch {
    return false;
  }
};

export const ensureApiEndpoint = (endpoint: string): string => {
  const normalized = endpoint.trim();
  if (!normalized) {
    return '';
  }

  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(normalized) || normalized.startsWith('//')) {
    throw new Error('Endpoint externo no permitido');
  }

  if (normalized.includes('..')) {
    throw new Error('Endpoint no permitido');
  }

  if (normalized.startsWith('/') || normalized.startsWith('?')) {
    return normalized;
  }

  return `/${normalized}`;
};

export const buildApiUrl = (path: string = ''): string => {
  if (!path) {
    return API_ORIGIN;
  }

  if (path.startsWith('http://') || path.startsWith('https://')) {
    if (!isAllowedApiUrl(path)) {
      throw new Error('URL no permitida para API');
    }
    return path;
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_ORIGIN}${normalizedPath}`;
};

const API_BASE_URL = buildApiUrl('/api');

interface ApiFetchOptions extends RequestInit {
  headers?: HeadersInit;
}

export const apiFetch = async <T = any>(
  endpoint: string, 
  options: ApiFetchOptions = {}
): Promise<T> => {
  const normalizedEndpoint = ensureApiEndpoint(endpoint);

  // Preparar headers según el tipo de body
  const headers: Record<string, string> = {
    ...options.headers as Record<string, string>,
  };

  // Buscar token en localStorage y agregarlo automáticamente
  const token = localStorage.getItem('token_acceso');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Solo agregar Content-Type si NO es FormData
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  // Si es FormData, el navegador establecerá automáticamente
  // el Content-Type con el boundary correcto

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${normalizedEndpoint}`, config);

    // Manejar error 401 (Unauthorized - Token expirado o inválido)
    if (response.status === 401) {
      console.warn('Token expirado o inválido. Redirigiendo al login...');
      // Limpiar localStorage
      localStorage.clear();
      // Redirigir al login
      window.location.href = '/login';
      throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
    }

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`HTTP ${response.status}:`, errorText);
      throw new Error(`Error HTTP: ${response.status} - ${errorText || response.statusText}`);
    }

    // Para DELETE (204 No Content) o respuestas vacías
    if (response.status === 204 || response.headers.get('content-length') === '0') {
      return {} as T;
    }

    return await response.json();
    
  } catch (error) {
    console.error("Error conectando con el backend:", error);
    throw error;
  }
};
