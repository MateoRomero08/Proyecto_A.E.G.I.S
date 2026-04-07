import { Badge } from "../app/components/ui/badge";

type RolVisual = "EMPLEADO" | "IMPLEMENTADOR" | "AUDITOR" | "LIDER_EQUIPO" | "CAPACITADOR";
type RolVisualResuelto = RolVisual | "SUPERADMIN";

type RoleBadgeProps = {
  rol?: string | null;
  isSuperuser?: boolean;
  isLeader?: boolean;
  className?: string;
};

const normalizarRol = (rol?: string | null): RolVisual | null => {
  if (!rol) {
    return null;
  }

  if (rol === "AUDITOR_INTERNO") {
    return "AUDITOR";
  }

  if (
    rol === "EMPLEADO"
    || rol === "IMPLEMENTADOR"
    || rol === "AUDITOR"
    || rol === "LIDER_EQUIPO"
    || rol === "CAPACITADOR"
  ) {
    return rol;
  }

  return null;
};

const ROLE_STYLES: Record<
  RolVisualResuelto,
  { label: string; badgeClassName: string; avatarClassName: string }
> = {
  SUPERADMIN: {
    label: "SuperAdmin",
    badgeClassName: "bg-black text-yellow-400 border border-yellow-500 font-bold",
    avatarClassName: "bg-black text-yellow-400 border border-yellow-500",
  },
  LIDER_EQUIPO: {
    label: "Lider de Equipo",
    badgeClassName: "bg-purple-100 text-purple-700 border-purple-300",
    avatarClassName: "bg-purple-100 text-purple-700 border border-purple-300",
  },
  AUDITOR: {
    label: "Auditor",
    badgeClassName: "bg-blue-100 text-blue-700 border-blue-300",
    avatarClassName: "bg-blue-100 text-blue-700 border border-blue-300",
  },
  IMPLEMENTADOR: {
    label: "Implementador",
    badgeClassName: "bg-orange-100 text-orange-700 border-orange-300",
    avatarClassName: "bg-orange-100 text-orange-700 border border-orange-300",
  },
  CAPACITADOR: {
    label: "Capacitador",
    badgeClassName: "bg-green-100 text-green-700 border-green-300",
    avatarClassName: "bg-green-100 text-green-700 border border-green-300",
  },
  EMPLEADO: {
    label: "Empleado",
    badgeClassName: "bg-gray-100 text-gray-700 border-gray-300",
    avatarClassName: "bg-gray-100 text-gray-700 border border-gray-300",
  },
};

const resolverRolVisual = (
  rol?: string | null,
  isSuperuser = false,
  isLeader = false,
): RolVisualResuelto => {
  if (isSuperuser) {
    return "SUPERADMIN";
  }

  const rolNormalizado = normalizarRol(rol);

  if (isLeader || rolNormalizado === "LIDER_EQUIPO") {
    return "LIDER_EQUIPO";
  }

  return rolNormalizado ?? "EMPLEADO";
};

export const obtenerNombreRol = (
  rol?: string | null,
  isSuperuser = false,
  isLeader = false,
): string => {
  const rolVisual = resolverRolVisual(rol, isSuperuser, isLeader);
  return ROLE_STYLES[rolVisual].label;
};

export const obtenerClasesAvatarRol = (
  rol?: string | null,
  isSuperuser = false,
  isLeader = false,
): string => {
  const rolVisual = resolverRolVisual(rol, isSuperuser, isLeader);
  return ROLE_STYLES[rolVisual].avatarClassName;
};

export function RoleBadge({ rol, isSuperuser = false, isLeader = false, className = "" }: RoleBadgeProps) {
  const rolVisual = resolverRolVisual(rol, isSuperuser, isLeader);
  const style = ROLE_STYLES[rolVisual];

  return <Badge className={`${style.badgeClassName} ${className}`.trim()}>{style.label}</Badge>;
}
