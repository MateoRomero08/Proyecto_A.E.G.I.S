// src/utils/api.ts

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_ORIGIN = API_URL.replace(/\/$/, '');

export const buildApiUrl = (path: string = ''): string => {
  if (!path) {
    return API_ORIGIN;
  }

  if (path.startsWith('http://') || path.startsWith('https://')) {
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
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

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
