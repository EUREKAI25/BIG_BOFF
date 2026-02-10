import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, Link } from 'react-router-dom';
import Logo from '../components/Logo';
import FloatingHearts from '../components/FloatingHearts';
import { useClickSound } from '../hooks/useClickSound';

type ViewState = 'generating' | 'choice' | 'send' | 'sent' | 'kept';

export default function PreviewPage() {
  const { t } = useTranslation();
  const { giftId: _giftId } = useParams(); // Will be used for API call
  const playClick = useClickSound();

  const [viewState, setViewState] = useState<ViewState>('generating');
  const [recipientName, setRecipientName] = useState('');
  const [recipientContact, setRecipientContact] = useState('');
  const [senderName, setSenderName] = useState('');
  const [isSending, setIsSending] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!recipientName.trim() || !recipientContact.trim()) return;

    setIsSending(true);
    // TODO: API call to send manifestation
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsSending(false);
    setViewState('sent');
  };

  const handleKeepForSelf = async () => {
    playClick();
    // TODO: API call to save for self
    await new Promise(resolve => setTimeout(resolve, 1000));
    setViewState('kept');
  };

  // GENERATING SCREEN - Waiting for video creation
  if (viewState === 'generating') {
    return (
      <div className="min-h-screen flex flex-col relative overflow-hidden">
        <div className="absolute inset-0 bg-love-primary" />
        <FloatingHearts count={12} />

        <header className="relative z-10 p-4 flex items-center justify-center">
          <Logo className="h-20" />
        </header>

        <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
          <div className="w-full max-w-sm text-center">
            {/* Animated heart */}
            <div className="w-24 h-24 mx-auto mb-8 relative">
              <div className="absolute inset-0 rounded-full bg-love-dark/30 animate-ping" />
              <div className="absolute inset-0 flex items-center justify-center">
                <svg className="w-16 h-16 text-cream" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                </svg>
              </div>
            </div>

            <h2 className="text-cream text-xl font-medium mb-3">
              {t('preview.generating')}
            </h2>
            <p className="text-cream/60 text-sm mb-6">
              {t('preview.generatingDesc')}
            </p>
            <p className="text-cream/40 text-xs italic">
              {t('preview.generatingTip')}
            </p>

            {/* Continue to send options anyway */}
            <button
              onClick={() => { playClick(); setViewState('choice'); }}
              className="btn-love w-full py-3 mt-10"
            >
              {t('preview.continue')}
            </button>
          </div>
        </main>
      </div>
    );
  }

  // CHOICE SCREEN - Send or keep
  if (viewState === 'choice') {
    return (
      <div className="min-h-screen flex flex-col relative overflow-hidden">
        <div className="absolute inset-0 bg-love-primary" />
        <FloatingHearts count={10} />

        <header className="relative z-10 p-4 flex items-center justify-between">
          <button
            onClick={() => { playClick(); setViewState('generating'); }}
            className="text-cream/60 hover:text-cream transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <Logo className="h-20" />
          <div className="w-6" />
        </header>

        <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
          <div className="w-full max-w-sm">
            <h2 className="text-cream text-xl font-medium text-center mb-8">
              {t('preview.whatToDo')}
            </h2>

            <div className="space-y-4">
              {/* Send to someone */}
              <button
                onClick={() => { playClick(); setViewState('send'); }}
                className="btn-love w-full p-5 rounded-3xl text-left"
              >
                <div className="flex items-center gap-4">
                  <svg className="w-6 h-6 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  <div>
                    <p className="font-semibold">{t('preview.sendToSomeone')}</p>
                    <p className="text-cream/60 text-sm">{t('preview.sendToSomeoneHint')}</p>
                  </div>
                </div>
              </button>

              {/* Keep for myself */}
              <button
                onClick={handleKeepForSelf}
                className="option-love w-full p-5 rounded-3xl text-left"
              >
                <div className="flex items-center gap-4">
                  <svg className="w-6 h-6 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                  <div>
                    <p className="font-semibold">{t('preview.keepForSelf')}</p>
                    <p className="text-cream/60 text-sm">{t('preview.keepForSelfHint')}</p>
                  </div>
                </div>
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // SEND FORM SCREEN
  if (viewState === 'send') {
    return (
      <div className="min-h-screen flex flex-col relative overflow-hidden">
        <div className="absolute inset-0 bg-love-primary" />
        <FloatingHearts count={8} />

        <header className="relative z-10 p-4 flex items-center justify-between">
          <button
            onClick={() => { playClick(); setViewState('choice'); }}
            className="text-cream/60 hover:text-cream transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <Logo className="h-20" />
          <div className="w-6" />
        </header>

        <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
          <div className="w-full max-w-sm">
            <h2 className="text-cream text-xl font-medium text-center mb-6">
              {t('preview.sendTitle')}
            </h2>

            <form onSubmit={handleSend} className="space-y-4">
              {/* Your name */}
              <div>
                <label className="block text-cream/80 text-sm mb-2">
                  {t('preview.yourName')}
                </label>
                <input
                  type="text"
                  value={senderName}
                  onChange={(e) => setSenderName(e.target.value)}
                  placeholder={t('preview.yourNamePlaceholder')}
                  className="input-love"
                  required
                />
              </div>

              {/* Recipient name */}
              <div>
                <label className="block text-cream/80 text-sm mb-2">
                  {t('preview.recipientName')}
                </label>
                <input
                  type="text"
                  value={recipientName}
                  onChange={(e) => setRecipientName(e.target.value)}
                  placeholder={t('preview.recipientNamePlaceholder')}
                  className="input-love"
                  required
                />
              </div>

              {/* Recipient contact */}
              <div>
                <label className="block text-cream/80 text-sm mb-2">
                  {t('preview.recipientContact')}
                </label>
                <input
                  type="text"
                  value={recipientContact}
                  onChange={(e) => setRecipientContact(e.target.value)}
                  placeholder={t('preview.recipientContactPlaceholder')}
                  className="input-love"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isSending || !recipientName.trim() || !recipientContact.trim() || !senderName.trim()}
                className="btn-love w-full py-3 mt-6 disabled:opacity-50"
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
                  t('preview.sendButton')
                )}
              </button>
            </form>
          </div>
        </main>
      </div>
    );
  }

  // SENT SUCCESS SCREEN
  if (viewState === 'sent') {
    return (
      <div className="min-h-screen flex flex-col relative overflow-hidden">
        <div className="absolute inset-0 bg-love-primary" />
        <FloatingHearts count={15} />

        <header className="relative z-10 p-4 flex items-center justify-center">
          <Logo className="h-20" />
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
              {t('preview.sentTitle')}
            </h2>
            <p className="text-cream/60 text-sm mb-8">
              {t('preview.sentDesc', { name: recipientName })}
            </p>

            <div className="space-y-3">
              <Link
                to="/create"
                className="btn-love w-full py-3 block text-center"
              >
                {t('preview.createAnother')}
              </Link>
              <Link
                to="/"
                className="text-cream/50 text-sm hover:text-cream transition-colors block"
              >
                {t('common.back')}
              </Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // KEPT FOR SELF SUCCESS SCREEN
  if (viewState === 'kept') {
    return (
      <div className="min-h-screen flex flex-col relative overflow-hidden">
        <div className="absolute inset-0 bg-love-primary" />
        <FloatingHearts count={15} />

        <header className="relative z-10 p-4 flex items-center justify-center">
          <Logo className="h-20" />
        </header>

        <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
          <div className="w-full max-w-sm text-center">
            {/* Heart icon */}
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-love-dark/50 flex items-center justify-center">
              <svg className="w-10 h-10 text-cream" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
              </svg>
            </div>

            <h2 className="text-cream text-2xl font-medium mb-2">
              {t('preview.keptTitle')}
            </h2>
            <p className="text-cream/60 text-sm mb-8">
              {t('preview.keptDesc')}
            </p>

            <div className="space-y-3">
              <Link
                to="/create"
                className="btn-love w-full py-3 block text-center"
              >
                {t('preview.createAnother')}
              </Link>
              <Link
                to="/"
                className="text-cream/50 text-sm hover:text-cream transition-colors block"
              >
                {t('common.back')}
              </Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return null;
}
