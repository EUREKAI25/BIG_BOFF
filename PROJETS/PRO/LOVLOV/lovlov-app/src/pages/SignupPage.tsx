import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, Link } from 'react-router-dom';
import Logo from '../components/Logo';
import FloatingHearts from '../components/FloatingHearts';
import { useClickSound } from '../hooks/useClickSound';

type Step = 'phone' | 'photos' | 'complete';

export default function SignupPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const playClick = useClickSound();

  const [step, setStep] = useState<Step>('phone');
  const [phone, setPhone] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [codeSent, setCodeSent] = useState(false);
  const [myPhoto, setMyPhoto] = useState<string | null>(null);
  const [partnerPhoto, setPartnerPhoto] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const myPhotoInputRef = useRef<HTMLInputElement>(null);
  const partnerPhotoInputRef = useRef<HTMLInputElement>(null);

  const handleSendCode = async () => {
    if (!phone.trim()) return;
    playClick();
    setIsVerifying(true);

    // TODO: API call to send verification code
    await new Promise(resolve => setTimeout(resolve, 1500));

    setIsVerifying(false);
    setCodeSent(true);
  };

  const handleVerifyCode = async () => {
    if (!verificationCode.trim()) return;
    playClick();
    setIsVerifying(true);

    // TODO: API call to verify code
    await new Promise(resolve => setTimeout(resolve, 1500));

    setIsVerifying(false);
    setStep('photos');
  };

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>, type: 'my' | 'partner') => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = () => {
      if (type === 'my') {
        setMyPhoto(reader.result as string);
      } else {
        setPartnerPhoto(reader.result as string);
      }
    };
    reader.readAsDataURL(file);
    playClick();
  };

  const handleComplete = async () => {
    if (!myPhoto) return;
    playClick();
    setIsSubmitting(true);

    // TODO: API call to save profile with photos
    await new Promise(resolve => setTimeout(resolve, 1500));

    setIsSubmitting(false);
    setStep('complete');
  };

  const handleGoToDashboard = () => {
    playClick();
    navigate('/dashboard');
  };

  // STEP 1: Phone verification
  if (step === 'phone') {
    return (
      <div className="min-h-screen flex flex-col relative overflow-hidden">
        <div className="absolute inset-0 bg-love-primary" />
        <FloatingHearts count={8} />

        <header className="relative z-10 p-4 flex items-center justify-between">
          <Link to="/" className="text-cream/60 hover:text-cream transition-colors">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <Logo className="h-16" />
          <div className="w-6" />
        </header>

        <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
          <div className="w-full max-w-sm">
            <h2 className="text-cream text-xl font-medium text-center mb-2">
              {t('signup.phoneTitle')}
            </h2>
            <p className="text-cream/60 text-sm text-center mb-8">
              {t('signup.phoneDesc')}
            </p>

            <div className="space-y-4">
              {/* Phone input */}
              <div>
                <label className="block text-cream/80 text-sm mb-2">
                  {t('signup.phoneLabel')}
                </label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder={t('signup.phonePlaceholder')}
                  className="input-love"
                  disabled={codeSent}
                />
              </div>

              {!codeSent ? (
                <button
                  onClick={handleSendCode}
                  disabled={isVerifying || !phone.trim()}
                  className="btn-love w-full py-3 disabled:opacity-50"
                >
                  {isVerifying ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      {t('common.loading')}
                    </span>
                  ) : (
                    t('signup.sendCode')
                  )}
                </button>
              ) : (
                <>
                  {/* Verification code input */}
                  <div>
                    <label className="block text-cream/80 text-sm mb-2">
                      {t('signup.codeLabel')}
                    </label>
                    <input
                      type="text"
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value)}
                      placeholder={t('signup.codePlaceholder')}
                      className="input-love text-center text-2xl tracking-widest"
                      maxLength={6}
                    />
                  </div>

                  <button
                    onClick={handleVerifyCode}
                    disabled={isVerifying || verificationCode.length < 4}
                    className="btn-love w-full py-3 disabled:opacity-50"
                  >
                    {isVerifying ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        {t('common.loading')}
                      </span>
                    ) : (
                      t('signup.verifyCode')
                    )}
                  </button>

                  <button
                    onClick={() => { setCodeSent(false); setVerificationCode(''); }}
                    className="text-cream/50 text-sm hover:text-cream transition-colors w-full text-center"
                  >
                    {t('signup.changePhone')}
                  </button>
                </>
              )}
            </div>
          </div>
        </main>
      </div>
    );
  }

  // STEP 2: Photo upload
  if (step === 'photos') {
    return (
      <div className="min-h-screen flex flex-col relative overflow-hidden">
        <div className="absolute inset-0 bg-love-primary" />
        <FloatingHearts count={8} />

        <header className="relative z-10 p-4 flex items-center justify-between">
          <button
            onClick={() => { playClick(); setStep('phone'); }}
            className="text-cream/60 hover:text-cream transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <Logo className="h-16" />
          <div className="w-6" />
        </header>

        <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
          <div className="w-full max-w-sm">
            <h2 className="text-cream text-xl font-medium text-center mb-2">
              {t('signup.photosTitle')}
            </h2>
            <p className="text-cream/60 text-sm text-center mb-8">
              {t('signup.photosDesc')}
            </p>

            <div className="space-y-6">
              {/* My photo */}
              <div>
                <label className="block text-cream/80 text-sm mb-3">
                  {t('signup.myPhotoLabel')} *
                </label>
                <input
                  ref={myPhotoInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => handlePhotoUpload(e, 'my')}
                  className="hidden"
                />
                <button
                  onClick={() => myPhotoInputRef.current?.click()}
                  className="w-full aspect-square max-w-[200px] mx-auto rounded-3xl border-2 border-dashed border-cream/30 flex flex-col items-center justify-center overflow-hidden hover:border-cream/50 transition-colors"
                >
                  {myPhoto ? (
                    <img src={myPhoto} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <>
                      <svg className="w-12 h-12 text-cream/40 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      <span className="text-cream/40 text-sm">{t('signup.addPhoto')}</span>
                    </>
                  )}
                </button>
              </div>

              {/* Partner photo (optional) */}
              <div>
                <label className="block text-cream/80 text-sm mb-3">
                  {t('signup.partnerPhotoLabel')}
                  <span className="text-cream/40 ml-1">({t('signup.optional')})</span>
                </label>
                <input
                  ref={partnerPhotoInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => handlePhotoUpload(e, 'partner')}
                  className="hidden"
                />
                <button
                  onClick={() => partnerPhotoInputRef.current?.click()}
                  className="w-full aspect-square max-w-[200px] mx-auto rounded-3xl border-2 border-dashed border-cream/30 flex flex-col items-center justify-center overflow-hidden hover:border-cream/50 transition-colors"
                >
                  {partnerPhoto ? (
                    <img src={partnerPhoto} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <>
                      <svg className="w-12 h-12 text-cream/40 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                      </svg>
                      <span className="text-cream/40 text-sm">{t('signup.addPartnerPhoto')}</span>
                    </>
                  )}
                </button>
                <p className="text-cream/40 text-xs text-center mt-2">
                  {t('signup.partnerPhotoHint')}
                </p>
              </div>

              <button
                onClick={handleComplete}
                disabled={isSubmitting || !myPhoto}
                className="btn-love w-full py-3 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    {t('common.loading')}
                  </span>
                ) : (
                  t('signup.continue')
                )}
              </button>

              <button
                onClick={() => { playClick(); setStep('complete'); }}
                className="text-cream/50 text-sm hover:text-cream transition-colors w-full text-center"
              >
                {t('signup.skipPhotos')}
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // STEP 3: Complete
  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute inset-0 bg-love-primary" />
      <FloatingHearts count={15} />

      <header className="relative z-10 p-4 flex items-center justify-center">
        <Logo className="h-16" />
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
            {t('signup.completeTitle')}
          </h2>
          <p className="text-cream/60 text-sm mb-8">
            {t('signup.completeDesc')}
          </p>

          <button
            onClick={handleGoToDashboard}
            className="btn-love w-full py-3"
          >
            {t('signup.createManifestation')}
          </button>
        </div>
      </main>
    </div>
  );
}
