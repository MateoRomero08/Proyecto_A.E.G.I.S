import { Navigate } from "react-router-dom";
import { esSuperusuario } from "../../utils/auth";

interface SuperAdminRouteProps {
  children: React.ReactNode;
}

export function SuperAdminRoute({ children }: SuperAdminRouteProps) {
  if (!esSuperusuario()) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
