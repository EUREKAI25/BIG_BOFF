import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, Link } from 'react-router-dom';
import Logo from '../components/Logo';
import FloatingHearts from '../components/FloatingHearts';
import { useClickSound } from '../hooks/useClickSound';

type ViewState = 'intro' | 'video' | 'actions' | 'message' | 'messageSent';
type Purpose = 'manifest' | 'seduce' | 'love';

// Mock video - in production, this will be the actual generated video
const mockVideo = {
  id: 1,
  type: 'image' as const,
  url: 'https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=1080&h=1920&fit=crop'
};

// Mock gift data - will come from API
const mockGift = {
  id: 'demo-123',
  senderName: 'Jean',
  purpose: 'love' as Purpose, // Options: manifest, seduce, love
};

export default function ViewerPage() {
  const { t } = useTranslation();
  const { giftId } = useParams();
  const playClick = useClickSound();

  const [viewState, setViewState] = useState<ViewState>('intro');
  const [showControls, setShowControls] = useState(true);
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);

  // Hide controls after inactivity (only in video mode)
  useEffect(() => {
    if (viewState !== 'video') return;
    const timer = setTimeout(() => setShowControls(false), 5000);
    return () => clearTimeout(timer);
  }, [showControls, viewState]);

  const handleClick = () => {
    if (viewState === 'video') {
      setShowControls(true);
    }
  };

  const startVideo = () => {
    playClick();
    setViewState('video');
  };

  const replayVideo = () => {
    playClick();
    setViewState('video');
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    setIsSending(true);
    // TODO: API call to send message
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsSending(false);
    setViewState('messageSent');
  };

  // Get purpose text based on the gift purpose
  const getPurposeText = () => {
    switch (mockGift.purpose) {
      case 'manifest':
        return t('viewer.purposeManifest');
      case 'seduce':
        return t('viewer.purposeSeduce');
      case 'love':
        return t('viewer.purposeLove');
      default:
        return t('viewer.purposeLove');
    }
  };

  // INTRO SCREEN
  if (viewState === 'intro') {
    return (
      <div className="min-h-screen flex flex-col relative overflow-hidden">
        <div className="absolute inset-0 bg-love-primary" />
        <FloatingHearts count={12} />

        <header className="relative z-10 p-4 flex items-center justify-center">
          <Logo className="h-8" />
        </header>

        <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 text-center">
          <div className="glass-love-light p-8 rounded-3xl max-w-sm">
            <p className="text-cream/70 text-sm mb-2">
              {mockGift.senderName}
            </p>
            <p className="text-cream text-xl font-medium mb-6">
              {getPurposeText()}
            </p>

            <button
              onClick={startVideo}
              className="btn-love w-full py-3"
            >
              {t('viewer.watchVideo')}
            </button>
          </div>

          {/* Explanation of LovLov */}
          <p className="text-cream/40 text-xs mt-8 max-w-xs">
            {t('app.explanation')}
          </p>
        </main>
      </div>
    );
  }

  // MESSAGE FORM SCREEN
  if (viewState === 'message') {
    return (
      <div className="min-h-screen flex flex-col relative overflow-hidden">
        <div className="absolute inset-0 bg-love-primary" />
        <FloatingHearts count={8} />

        <header className="relative z-10 p-4 flex items-center justify-between">
          <button
            onClick={() => { playClick(); setViewState('actions'); }}
            className="text-cream/60 hover:text-cream transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <Logo className="h-8" />
          <div className="w-6" />
        </header>

        <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
          <div className="w-full max-w-sm">
            <h2 className="text-cream text-xl font-medium text-center mb-2">
              {t('viewer.messageTitle', { name: mockGift.senderName })}
            </h2>
            <p className="text-cream/60 text-sm text-center mb-6">
              {t('viewer.messageFree')}
            </p>

            <form onSubmit={handleSendMessage} className="space-y-4">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={t('viewer.messagePlaceholder')}
                rows={5}
                className="input-love resize-none"
                required
              />

              <button
                type="submit"
                disabled={isSending || !message.trim()}
                className="btn-love w-full py-3 disabled:opacity-50"
              >
                {isSending ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    {t('common.loading')}
                  </span>
                ) : (
                  t('viewer.sendFree')
                )}
              </button>
            </form>
          </div>
        </main>
      </div>
    );
  }

  // MESSAGE SENT SUCCESS SCREEN
  if (viewState === 'messageSent') {
    return (
      <div className="min-h-screen flex flex-col relative overflow-hidden">
        <div className="absolute inset-0 bg-love-primary" />
        <FloatingHearts count={15} />

        <header className="relative z-10 p-4 flex items-center justify-center">
          <Logo className="h-8" />
        </header>

        <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
          <div className="w-full max-w-sm text-center">
            {/* Success icon */}
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-love-dark/50 flex items-center justify-center">
              <svg className="w-10 h-10 text-cream" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>

            <h2 className="text-cream text-2xl font-medium mb-2">
              {t('viewer.messageSentTitle')}
            </h2>
            <p className="text-cream/60 text-sm mb-8">
              {t('viewer.messageSentDesc', { name: mockGift.senderName })}
            </p>

            {/* Encourage signup */}
            <div className="glass-love-light p-6 rounded-3xl mb-6">
              <p className="text-cream text-sm mb-4">
                {t('viewer.signupEncourage')}
              </p>
              <Link
                to="/create"
                onClick={() => playClick()}
                className="btn-love w-full py-3 block text-center"
              >
                {t('viewer.createMyOwn')}
              </Link>
            </div>

            <Link
              to="/"
              className="text-cream/50 text-sm hover:text-cream transition-colors"
            >
              {t('common.back')}
            </Link>
          </div>
        </main>
      </div>
    );
  }

  // ACTIONS SCREEN (after video)
  if (viewState === 'actions') {
    return (
      <div className="min-h-screen flex flex-col relative overflow-hidden">
        <div className="absolute inset-0 bg-love-primary" />
        <FloatingHearts count={10} />

        <header className="relative z-10 p-4 flex items-center justify-between">
          <button
            onClick={replayVideo}
            className="text-cream/60 hover:text-cream transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          <Logo className="h-8" />
          <div className="w-6" />
        </header>

        <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
          <div className="w-full max-w-sm">
            <h2 className="text-cream text-xl font-medium text-center mb-6">
              {t('viewer.whatToDo')}
            </h2>

            <div className="space-y-3">
              {/* Send a message - FREE */}
              <button
                onClick={() => { playClick(); setViewState('message'); }}
                className="btn-love w-full text-left p-4"
              >
                <div className="flex items-center gap-3">
                  <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <div>
                    <p className="font-medium">{t('viewer.replyFreeMessage')}</p>
                    <p className="text-cream/60 text-xs">{t('viewer.replyFreeHint')}</p>
                  </div>
                </div>
              </button>

              {/* Send your video to them - FREE (paid by sender) */}
              <Link
                to={`/create/${giftId}`}
                onClick={() => playClick()}
                className="btn-love w-full text-left p-4 block"
              >
                <div className="flex items-center gap-3">
                  <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <div>
                    <p className="font-medium">{t('viewer.replyFreeVideo')}</p>
                    <p className="text-cream/60 text-xs">{t('viewer.replyFreeVideoHint', { name: mockGift.senderName })}</p>
                  </div>
                </div>
              </Link>

              {/* Create your own */}
              <Link
                to="/create"
                onClick={() => playClick()}
                className="option-love w-full text-left p-4 block"
              >
                <div className="flex items-center gap-3">
                  <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  <div>
                    <p className="font-medium">{t('viewer.createOwn')}</p>
                    <p className="text-cream/60 text-xs">{t('viewer.createOwnHint')}</p>
                  </div>
                </div>
              </Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // VIDEO VIEWER (single video)
  return (
    <div
      className="h-screen w-screen bg-black relative overflow-hidden"
      onClick={handleClick}
    >
      {/* Video/Image */}
      <div className="absolute inset-0">
        <img
          src={mockVideo.url}
          alt=""
          className="w-full h-full object-cover"
        />
      </div>

      {/* Overlay gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/50 pointer-events-none" />

      {/* Header */}
      <div
        className={`absolute top-0 left-0 right-0 p-4 z-20 transition-opacity duration-300 flex items-center justify-between ${
          showControls ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <button
          onClick={() => setViewState('intro')}
          className="glass-love w-10 h-10 rounded-full flex items-center justify-center text-cream"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <Logo className="h-8" />
        <div className="w-10" />
      </div>

      {/* Sender info & Continue button */}
      <div
        className={`absolute bottom-0 left-0 right-0 p-6 z-20 transition-opacity duration-300 ${
          showControls ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <p className="text-cream/70 text-sm mb-4">{t('viewer.from')} {mockGift.senderName}</p>

        <button
          onClick={() => { playClick(); setViewState('actions'); }}
          className="btn-love w-full py-3"
        >
          {t('viewer.continue')}
        </button>
      </div>
    </div>
  );
}
