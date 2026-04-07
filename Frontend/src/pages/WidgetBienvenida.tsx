import { Shield, Sparkles } from "lucide-react";

interface WidgetBienvenidaProps {
  nombre: string;
  rol: string;
  empresaNombre?: string | null;
}

export function WidgetBienvenida({ nombre, rol, empresaNombre }: WidgetBienvenidaProps) {
  return (
    <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Bienvenido, {nombre}</h2>
          <p className="text-gray-600 mt-1">
            Rol activo: <span className="font-semibold text-gray-900">{rol}</span>
          </p>
          {empresaNombre && (
            <p className="text-sm text-gray-500 mt-2">Empresa: {empresaNombre}</p>
          )}
        </div>

        <div className="inline-flex items-center gap-2 bg-slate-900 text-white px-3 py-2 rounded-lg text-sm font-medium">
          <Shield className="w-4 h-4" />
          AEGIS
        </div>
      </div>

      <div className="mt-4 inline-flex items-center gap-2 text-sm text-slate-600 bg-slate-100 px-3 py-2 rounded-lg">
        <Sparkles className="w-4 h-4 text-yellow-600" />
        Tu panel se adapta dinámicamente según tus permisos RBAC.
      </div>
    </section>
  );
}
