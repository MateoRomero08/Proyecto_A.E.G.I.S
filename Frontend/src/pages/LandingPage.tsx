import { Navbar } from '../app/components/Navbar';
import { Hero } from '../app/components/Hero';
import { Features } from '../app/components/Features';
import { Footer } from '../app/components/Footer';

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <Hero />
      <Features />
      <Footer />
    </div>
  );
}
