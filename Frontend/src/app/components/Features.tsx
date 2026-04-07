import { Shield, BookOpen, ClipboardCheck, Users, TrendingUp, Lock } from 'lucide-react';

export function Features() {
  const features = [
    {
      icon: Shield,
      title: 'Implementación ISO 27001',
      description: 'Implementa los controles de seguridad de la información de manera estructurada y eficiente. Cumple con todos los requisitos de la norma.',
      color: 'from-blue-500 to-blue-600',
      iconBg: 'bg-blue-500/10',
      iconColor: 'text-blue-500',
    },
    {
      icon: BookOpen,
      title: 'Capacitación Continua',
      description: 'Programa de formación integral para tu equipo. Material actualizado, evaluaciones y seguimiento de progreso en tiempo real.',
      color: 'from-yellow-500 to-yellow-600',
      iconBg: 'bg-yellow-500/10',
      iconColor: 'text-yellow-500',
    },
    {
      icon: ClipboardCheck,
      title: 'Auditoría y Cumplimiento',
      description: 'Realiza auditorías internas, gestiona hallazgos y monitorea el cumplimiento normativo con reportes automáticos y detallados.',
      color: 'from-green-500 to-green-600',
      iconBg: 'bg-green-500/10',
      iconColor: 'text-green-500',
    },
    {
      icon: Users,
      title: 'Gestión de Usuarios',
      description: 'Control completo de roles, permisos y accesos. Administra tu equipo de manera centralizada y segura.',
      color: 'from-purple-500 to-purple-600',
      iconBg: 'bg-purple-500/10',
      iconColor: 'text-purple-500',
    },
    {
      icon: TrendingUp,
      title: 'Reportes Avanzados',
      description: 'Análisis profundo con dashboards interactivos. Visualiza métricas clave, KPIs y tendencias de cumplimiento.',
      color: 'from-pink-500 to-pink-600',
      iconBg: 'bg-pink-500/10',
      iconColor: 'text-pink-500',
    },
    {
      icon: Lock,
      title: 'Seguridad Garantizada',
      description: 'Cifrado end-to-end, autenticación multifactor y cumplimiento con las mejores prácticas de seguridad de la información.',
      color: 'from-indigo-500 to-indigo-600',
      iconBg: 'bg-indigo-500/10',
      iconColor: 'text-indigo-500',
    },
  ];

  return (
    <section id="features" className="py-24 bg-gradient-to-b from-white to-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Encabezado de sección */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4 leading-tight">
            Todo lo que necesitas para
            <span className="block bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              satisfacer tu cumplimiento ISO 27001
            </span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto text-justify">
            Una suite completa de herramientas diseñadas para facilitar tu camino 
            hacia la certificación ISO 27001 y mantener el cumplimiento continuo.
            <br /><br />
            Sabemos que gestionar la norma ISO 27001 puede ser abrumador. 
            Por eso creamos A.E.G.I.S.: una herramienta con enfoque humano y de alta calidad diseñada para hacerle la vida más fácil
            a las empresas y a los profesionales de la seguridad.
            Centraliza tus evidencias, realiza auditorías sin estrés y capacita a tu equipo en un entorno intuitivo. Nosotros te damos el control, el conocimiento y las constancias de aprendizaje para que tú te enfoques en lo que realmente importa: proteger tu información y alcanzar la certificación.
          </p>
        </div>

        {/* Grid de características */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="group relative bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border border-gray-100"
              >
                {/* Icono */}
                <div className={`inline-flex items-center justify-center w-14 h-14 ${feature.iconBg} rounded-xl mb-6 group-hover:scale-110 transition-transform`}>
                  <Icon className={`w-7 h-7 ${feature.iconColor}`} />
                </div>

                {/* Contenido */}
                <h3 className="text-2xl font-bold text-gray-900 mb-4">
                  {feature.title}
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  {feature.description}
                </p>

                {/* Gradiente decorativo */}
                <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${feature.color} rounded-t-2xl opacity-0 group-hover:opacity-100 transition-opacity`} />
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
