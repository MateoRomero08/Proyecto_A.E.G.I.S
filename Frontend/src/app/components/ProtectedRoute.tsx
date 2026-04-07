import { Navigate } from 'react-router-dom';
import { useLocation } from 'react-router-dom';
import { obtenerToken, obtenerUsuario, tieneAccesoRutaDashboard, tienePermisoUsuario } from '../../utils/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  permission?: string | string[];
}

/**
 * Componente de protección de rutas privadas.
 * 
 * Garantiza que solo usuarios autenticados con token válido
 * puedan acceder a las rutas protegidas.
 * 
 * Seguridad:
 * - Verifica existencia de token en localStorage
 * - Redirige a login si no hay token (previene acceso manual por URL)
 * - Usa replace para evitar que el usuario regrese con el botón atrás
 */
export function ProtectedRoute({ children, permission }: ProtectedRouteProps) {
  const location = useLocation();
  const token = obtenerToken();
  const usuario = obtenerUsuario();

  // Si no hay token, redirigir a login
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (!usuario) {
    return <Navigate to="/login" replace />;
  }

  const isApproved = Boolean(usuario.is_superuser || usuario.is_approved);

  if (location.pathname.startsWith('/dashboard') && !isApproved) {
    return <Navigate to="/espera" replace />;
  }

  if (location.pathname === '/espera' && isApproved) {
    return <Navigate to="/dashboard" replace />;
  }

  if (location.pathname.startsWith('/dashboard') && !tieneAccesoRutaDashboard(location.pathname, usuario)) {
    return <Navigate to="/dashboard" replace />;
  }

  if (permission && !tienePermisoUsuario(permission, usuario)) {
    return <Navigate to="/dashboard" replace />;
  }

  // Token existe, permitir acceso
  return <>{children}</>;
}
