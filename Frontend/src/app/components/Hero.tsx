import { Link } from 'react-router-dom';
import { ArrowRight, PlayCircle } from 'lucide-react';

export function Hero() {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 overflow-hidden">
      {/* Patrón de fondo decorativo */}
      <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:50px_50px]" />
      <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent" />
      
      {/* Contenido */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        {/* Badge */}
        <div className="inline-flex items-center px-4 py-2 mb-8 bg-yellow-400/10 border border-yellow-400/20 rounded-full">
          <span className="text-yellow-400 text-sm font-semibold">
            ✨ Solución Certificada ISO 27001
          </span>
        </div>

        {/* Título principal */}
        <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
          Gestión de Seguridad
          <span className="block bg-gradient-to-r from-yellow-400 to-yellow-600 bg-clip-text text-transparent">
            ISO 27001
          </span>
          Simplificada
        </h1>

        {/* Subtítulo */}
        <p className="text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
          AEGIS es tu plataforma integral para implementar, gestionar y mantener 
          el cumplimiento normativo ISO 27001. Auditorías, capacitación y reportes 
          en un solo lugar.
        </p>

        {/* Botones CTA */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link
            to="/registro"
            className="group px-8 py-4 bg-yellow-400 text-black font-bold text-lg rounded-lg hover:bg-yellow-500 transition-all duration-300 shadow-lg shadow-yellow-400/50 hover:shadow-yellow-400/70 hover:scale-105 flex items-center gap-2"
          >
            Comienza ahora
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          
          <button
            onClick={() => {
              document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
            }}
            className="group px-8 py-4 bg-white/10 backdrop-blur-sm text-white font-bold text-lg rounded-lg border-2 border-white/20 hover:bg-white/20 transition-all duration-300 flex items-center gap-2"
          >
            <PlayCircle className="w-5 h-5" />
            Saber más
          </button>
        </div>

        {/* Estadísticas */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10">
            <div className="text-4xl font-bold text-yellow-400 mb-2">100%</div>
            <div className="text-gray-300">Cumplimiento Normativo</div>
          </div>
          <div className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10">
            <div className="text-4xl font-bold text-yellow-400 mb-2">24/7</div>
            <div className="text-gray-300">Monitoreo Continuo</div>
          </div>
          <div className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10">
            <div className="text-4xl font-bold text-yellow-400 mb-2">500+</div>
            <div className="text-gray-300">Empresas Certificadas</div>
          </div>
        </div>
      </div>

      {/* Efecto de brillo */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-yellow-400/10 rounded-full blur-3xl" />
    </section>
  );
}
