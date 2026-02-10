import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import Logo from '../components/Logo';
import FloatingHearts from '../components/FloatingHearts';
import { useClickSound } from '../hooks/useClickSound';

export default function ReceivedPage() {
  const { t } = useTranslation();
  const { code: _code } = useParams(); // Will be used for API call
  const navigate = useNavigate();
  const playClick = useClickSound();
  const [isRevealing, setIsRevealing] = useState(false);
  const [showEnvelope, setShowEnvelope] = useState(true);

  // Mock gift data - will come from API
  const gift = {
    id: 'demo-123',
    senderName: 'Jean',
    recipientName: 'Marie',
  };

  const handleReveal = async () => {
    playClick();
    setIsRevealing(true);

    // Animate envelope opening
    await new Promise((resolve) => setTimeout(resolve, 800));
    setShowEnvelope(false);

    // Navigate to viewer after animation
    await new Promise((resolve) => setTimeout(resolve, 500));
    navigate(`/view/${gift.id}`);
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-love-primary" />

      {/* Floating hearts */}
      <FloatingHearts count={15} />

      {/* Header with logo */}
      <header className="relative z-10 p-4 flex items-center justify-center">
        <Logo className="h-8" />
      </header>

      {/* Main content */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">

        {showEnvelope ? (
          <>
            {/* Envelope with heart */}
            <div
              className={`relative cursor-pointer transition-all duration-700 ${
                isRevealing ? 'scale-150 opacity-0' : 'scale-100 opacity-100'
              }`}
              onClick={handleReveal}
            >
              {/* Envelope body - neumorphism style */}
              <div className="w-64 h-44 sm:w-72 sm:h-48 relative">
                {/* Envelope back with neumorphism */}
                <div
                  className="absolute inset-0 rounded-3xl"
                  style={{
                    background: 'var(--love-primary)',
                    boxShadow: `
                      8px 8px 16px rgba(80, 10, 0, 0.5),
                      -8px -8px 16px rgba(200, 40, 20, 0.25),
                      inset 0 0 30px rgba(245, 230, 211, 0.05)
                    `,
                    border: '1px solid rgba(245, 230, 211, 0.1)'
                  }}
                />

                {/* Envelope flap (top triangle) */}
                <div
                  className={`absolute inset-x-0 top-0 h-20 overflow-hidden transition-transform duration-500 origin-top ${
                    isRevealing ? '-rotate-x-180' : ''
                  }`}
                  style={{ perspective: '500px' }}
                >
                  <div
                    className="absolute inset-x-0 top-0 h-40 rounded-t-3xl"
                    style={{
                      background: 'linear-gradient(180deg, rgba(212, 111, 102, 0.3) 0%, rgba(182, 22, 0, 0.1) 100%)',
                      clipPath: 'polygon(0 0, 50% 100%, 100% 0)',
                      border: '1px solid rgba(245, 230, 211, 0.15)'
                    }}
                  />
                </div>

                {/* Heart in center */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative">
                    <img
                      src="/heart.svg"
                      alt=""
                      className="w-20 h-20 sm:w-24 sm:h-24 animate-heartbeat drop-shadow-lg"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Text below envelope */}
            <div className="mt-10 text-center">
              <p className="text-cream/70 text-sm sm:text-base mb-3">
                {t('gift.youReceived')}
              </p>
              <p className="font-romantic text-2xl sm:text-3xl text-cream">
                {t('gift.from')} <span className="text-love-light">{gift.senderName}</span>
              </p>
            </div>

            {/* Tap instruction */}
            <p className="mt-14 text-cream/40 text-sm animate-pulse">
              {t('gift.tapToOpen')}
            </p>
          </>
        ) : (
          /* Heart expanding animation before redirect */
          <div className="animate-ping">
            <img src="/heart.svg" alt="" className="w-28 h-28" />
          </div>
        )}
      </main>
    </div>
  );
}
