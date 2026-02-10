import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Logo from '../components/Logo';
import FloatingHearts from '../components/FloatingHearts';

export default function GiftPage() {
  const { t } = useTranslation();
  const { code: _code } = useParams(); // Will be used for API call
  const navigate = useNavigate();
  const [isOpening, setIsOpening] = useState(false);
  const [showReplyOptions, setShowReplyOptions] = useState(false);

  // Mock gift data
  const gift = {
    id: 'demo-123',
    senderName: 'Jean',
    recipientName: 'Marie',
  };

  const handleOpen = async () => {
    setIsOpening(true);
    // Simulate loading
    await new Promise((resolve) => setTimeout(resolve, 1500));
    // Navigate to viewer
    navigate(`/view/${gift.id}`);
  };

  const handleReplyToSender = () => {
    navigate(`/create/${gift.id}`);
  };

  const handleCreateForOther = () => {
    navigate('/create');
  };

  if (showReplyOptions) {
    return (
      <div className="min-h-screen flex flex-col relative overflow-hidden">
        <div className="absolute inset-0 bg-love-primary" />
        <FloatingHearts count={10} />

        <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
          <Logo className="w-20 h-20 mb-8" />

          <h2 className="font-elegant text-2xl text-cream text-center mb-8">
            {t('gift.replyTitle')}
          </h2>

          <div className="w-full max-w-sm space-y-4">
            {/* Reply to sender */}
            <button
              onClick={handleReplyToSender}
              className="glass-love w-full p-6 rounded-2xl text-left hover:bg-white/10 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-love-light/30 flex items-center justify-center">
                  <svg className="w-6 h-6 text-cream" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                  </svg>
                </div>
                <div>
                  <p className="text-cream font-semibold">
                    {t('gift.replyToSender')} {gift.senderName}
                  </p>
                  <p className="text-cream/60 text-sm">
                    Créer une déclaration en retour
                  </p>
                </div>
              </div>
            </button>

            {/* Create for someone else */}
            <button
              onClick={handleCreateForOther}
              className="glass-love w-full p-6 rounded-2xl text-left hover:bg-white/10 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-love-light/30 flex items-center justify-center">
                  <svg className="w-6 h-6 text-cream" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <div>
                  <p className="text-cream font-semibold">
                    {t('gift.createForSomeone')}
                  </p>
                  <p className="text-cream/60 text-sm">
                    Déclarer votre amour à quelqu'un
                  </p>
                </div>
              </div>
            </button>
          </div>

          <button
            onClick={() => setShowReplyOptions(false)}
            className="mt-8 text-cream/60 hover:text-cream transition-colors"
          >
            {t('common.back')}
          </button>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-love-primary" />
      <FloatingHearts count={15} />

      {/* Main */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
        {/* Gift envelope animation */}
        <div className="relative mb-8">
          <div
            className={`transform transition-all duration-700 ${
              isOpening ? 'scale-150 opacity-0' : 'scale-100 opacity-100'
            }`}
          >
            {/* Envelope */}
            <div className="glass-love w-64 h-48 rounded-3xl flex items-center justify-center relative overflow-hidden">
              <Logo className="w-20 h-20 animate-heartbeat" />

              {/* Envelope flap */}
              <div className="absolute inset-x-0 top-0 h-1/2 bg-love-light/20 origin-bottom transform -skew-y-6" />
            </div>
          </div>
        </div>

        {/* Text */}
        <div className="text-center mb-8">
          <p className="text-cream/80 text-lg mb-2">
            {t('gift.youReceived')}
          </p>
          <p className="font-romantic text-3xl text-love-gradient">
            {t('gift.from')} {gift.senderName}
          </p>
        </div>

        {/* Open button */}
        <button
          onClick={handleOpen}
          disabled={isOpening}
          className="btn-love text-lg px-10 py-4 rounded-full animate-heartbeat"
        >
          {isOpening ? (
            <span className="flex items-center gap-2">
              <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {t('common.loading')}
            </span>
          ) : (
            t('gift.openButton')
          )}
        </button>
      </main>

      {/* Footer link */}
      <footer className="relative z-10 p-6 text-center">
        <Link
          to="/create"
          className="text-cream/60 hover:text-cream transition-colors text-sm"
        >
          {t('viewer.createOwn')}
        </Link>
      </footer>
    </div>
  );
}
