import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import Logo from '../components/Logo';
import FloatingHearts from '../components/FloatingHearts';

export default function HomePage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      {/* Background - dark gradient */}
      <div className="absolute inset-0 bg-love-primary" />

      {/* Floating hearts background */}
      <FloatingHearts count={15} />

      {/* Main content - centered */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
        {/* Big Logo - adapts to user language */}
        <div className="mb-12">
          <Logo className="w-72 sm:w-96 md:w-[500px] h-auto" />
        </div>

        {/* CTA Button */}
        <Link
          to="/signup"
          className="btn-love text-lg px-10 py-4 rounded-full shadow-2xl"
        >
          {t('home.createButton')}
        </Link>
      </main>

      {/* Minimal footer */}
      <footer className="relative z-10 p-4 text-center text-cream/30 text-xs">
        LovLov
      </footer>
    </div>
  );
}
