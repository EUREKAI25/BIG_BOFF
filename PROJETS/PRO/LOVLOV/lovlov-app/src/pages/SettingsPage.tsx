import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import FloatingHearts from '../components/FloatingHearts';
import { useClickSound } from '../hooks/useClickSound';

export default function SettingsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const playClick = useClickSound();

  // Mock user data - will come from API/auth context
  const [user, setUser] = useState({
    phone: '+33 6 12 34 56 78',
    myPhoto: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&h=200&fit=crop',
    partnerPhoto: null as string | null,
  });

  const myPhotoInputRef = useRef<HTMLInputElement>(null);
  const partnerPhotoInputRef = useRef<HTMLInputElement>(null);

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>, type: 'my' | 'partner') => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = () => {
      if (type === 'my') {
        setUser(prev => ({ ...prev, myPhoto: reader.result as string }));
      } else {
        setUser(prev => ({ ...prev, partnerPhoto: reader.result as string }));
      }
      // TODO: API call to update photo
    };
    reader.readAsDataURL(file);
    playClick();
  };

  const handleLogout = () => {
    playClick();
    // TODO: Clear auth state
    navigate('/');
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute inset-0 bg-love-primary" />
      <FloatingHearts count={5} />

      {/* Header */}
      <header className="relative z-10 px-6 py-4 flex items-center justify-between">
        <button
          onClick={() => { playClick(); navigate(-1); }}
          className="text-cream/60 hover:text-cream transition-colors"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="text-xl font-semibold text-cream">
          {t('settings.title')}
        </h1>
        <div className="w-6" />
      </header>

      {/* Content */}
      <main className="relative z-10 flex-1 px-6 py-4 overflow-y-auto">
        <div className="max-w-md mx-auto space-y-6">

          {/* Profile section */}
          <section>
            <h2 className="text-cream/60 text-sm font-medium mb-3 uppercase tracking-wide">
              {t('settings.profile')}
            </h2>

            <div className="glass-love-light rounded-2xl p-4 space-y-4">
              {/* Phone */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-cream/60 text-sm">{t('settings.phone')}</p>
                  <p className="text-cream">{user.phone}</p>
                </div>
              </div>

              {/* My photo */}
              <div>
                <p className="text-cream/60 text-sm mb-2">{t('settings.myPhoto')}</p>
                <input
                  ref={myPhotoInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => handlePhotoUpload(e, 'my')}
                  className="hidden"
                />
                <button
                  onClick={() => myPhotoInputRef.current?.click()}
                  className="w-20 h-20 rounded-2xl border-2 border-dashed border-cream/30 flex items-center justify-center overflow-hidden hover:border-cream/50 transition-colors"
                >
                  {user.myPhoto ? (
                    <img src={user.myPhoto} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <svg className="w-8 h-8 text-cream/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  )}
                </button>
              </div>

              {/* Partner photo */}
              <div>
                <p className="text-cream/60 text-sm mb-2">
                  {t('settings.partnerPhoto')}
                  <span className="text-cream/30 ml-1">({t('signup.optional')})</span>
                </p>
                <input
                  ref={partnerPhotoInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => handlePhotoUpload(e, 'partner')}
                  className="hidden"
                />
                <button
                  onClick={() => partnerPhotoInputRef.current?.click()}
                  className="w-20 h-20 rounded-2xl border-2 border-dashed border-cream/30 flex items-center justify-center overflow-hidden hover:border-cream/50 transition-colors"
                >
                  {user.partnerPhoto ? (
                    <img src={user.partnerPhoto} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <svg className="w-8 h-8 text-cream/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          </section>

          {/* About section */}
          <section>
            <h2 className="text-cream/60 text-sm font-medium mb-3 uppercase tracking-wide">
              {t('settings.about')}
            </h2>

            <div className="glass-love-light rounded-2xl overflow-hidden">
              <button className="w-full px-4 py-3 flex items-center justify-between hover:bg-cream/5 transition-colors">
                <span className="text-cream">{t('settings.howItWorks')}</span>
                <svg className="w-5 h-5 text-cream/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
              <div className="h-px bg-cream/10" />
              <button className="w-full px-4 py-3 flex items-center justify-between hover:bg-cream/5 transition-colors">
                <span className="text-cream">{t('settings.privacy')}</span>
                <svg className="w-5 h-5 text-cream/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
              <div className="h-px bg-cream/10" />
              <button className="w-full px-4 py-3 flex items-center justify-between hover:bg-cream/5 transition-colors">
                <span className="text-cream">{t('settings.terms')}</span>
                <svg className="w-5 h-5 text-cream/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </section>

          {/* Logout */}
          <section>
            <button
              onClick={handleLogout}
              className="w-full px-4 py-3 rounded-2xl glass-love-light text-love-light hover:bg-cream/10 transition-colors"
            >
              {t('settings.logout')}
            </button>
          </section>

          {/* Version */}
          <p className="text-center text-cream/30 text-xs">
            LovLov v1.0.0
          </p>
        </div>
      </main>
    </div>
  );
}
