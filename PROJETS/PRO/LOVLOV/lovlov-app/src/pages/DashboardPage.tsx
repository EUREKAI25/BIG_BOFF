import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import FloatingHearts from '../components/FloatingHearts';
import { useClickSound } from '../hooks/useClickSound';

type ManifestationStatus = 'generating' | 'ready' | 'sent' | 'viewed';
type Filter = 'all' | 'personal' | 'sent';

interface Manifestation {
  id: string;
  purpose: 'manifest' | 'seduce' | 'love';
  status: ManifestationStatus;
  recipientName?: string;
  createdAt: Date;
  thumbnailUrl?: string;
}

// Mock data - will come from API
const mockManifestations: Manifestation[] = [
  {
    id: '1',
    purpose: 'love',
    status: 'sent',
    recipientName: 'Marie',
    createdAt: new Date('2025-02-05'),
    thumbnailUrl: 'https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=200&h=200&fit=crop',
  },
  {
    id: '2',
    purpose: 'manifest',
    status: 'ready',
    createdAt: new Date('2025-02-03'),
    thumbnailUrl: 'https://images.unsplash.com/photo-1516589178581-6cd7833ae3b2?w=200&h=200&fit=crop',
  },
  {
    id: '3',
    purpose: 'seduce',
    status: 'generating',
    recipientName: 'Sophie',
    createdAt: new Date('2025-02-06'),
  },
];

export default function DashboardPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const playClick = useClickSound();

  const [manifestations, setManifestations] = useState<Manifestation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>('all');

  useEffect(() => {
    loadManifestations();
  }, []);

  const loadManifestations = async () => {
    setIsLoading(true);
    // TODO: API call
    await new Promise(resolve => setTimeout(resolve, 800));
    setManifestations(mockManifestations);
    setIsLoading(false);
  };

  const filteredManifestations = manifestations.filter((m) => {
    if (filter === 'all') return true;
    if (filter === 'personal') return !m.recipientName;
    if (filter === 'sent') return !!m.recipientName;
    return true;
  });

  const getStatusBadge = (status: ManifestationStatus) => {
    switch (status) {
      case 'generating':
        return (
          <span className="inline-flex items-center gap-1 text-xs bg-love-light/20 text-love-light px-2 py-0.5 rounded-full">
            <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {t('dashboard.statusGenerating')}
          </span>
        );
      case 'ready':
        return (
          <span className="inline-flex items-center gap-1 text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
            </svg>
            {t('dashboard.statusReady')}
          </span>
        );
      case 'sent':
        return (
          <span className="inline-flex items-center gap-1 text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            {t('dashboard.statusSent')}
          </span>
        );
      case 'viewed':
        return (
          <span className="inline-flex items-center gap-1 text-xs bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded-full">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            {t('dashboard.statusViewed')}
          </span>
        );
    }
  };

  const getPurposeLabel = (purpose: string) => {
    return t(`create.purposes.${purpose}`);
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute inset-0 bg-love-primary" />
      <FloatingHearts count={6} />

      {/* Header */}
      <header className="relative z-10 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-cream">
          {t('dashboard.title')}
        </h1>
        <button
          onClick={() => { playClick(); navigate('/settings'); }}
          className="p-2 rounded-xl bg-cream/5 hover:bg-cream/10 transition-colors"
        >
          <svg className="w-5 h-5 text-cream" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </header>

      {/* Filter tabs */}
      <div className="relative z-10 flex gap-2 px-6 mb-4">
        {[
          { key: 'all', label: t('dashboard.filterAll') },
          { key: 'personal', label: t('dashboard.filterPersonal') },
          { key: 'sent', label: t('dashboard.filterSent') },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => { playClick(); setFilter(tab.key as Filter); }}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
              filter === tab.key
                ? 'option-love-selected'
                : 'option-love'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Manifestations list */}
      <main className="relative z-10 flex-1 px-6 pb-24 overflow-y-auto">
        {isLoading ? (
          <div className="flex justify-center py-12">
            <svg className="w-8 h-8 animate-spin text-cream/40" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : filteredManifestations.length === 0 ? (
          <div className="text-center py-12">
            <svg className="w-12 h-12 text-cream/20 mx-auto mb-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
            </svg>
            <p className="text-cream/60">
              {t('dashboard.noManifestations')}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredManifestations.map((manifestation) => (
              <button
                key={manifestation.id}
                onClick={() => { playClick(); navigate(`/manifestation/${manifestation.id}`); }}
                className="w-full glass-love-light p-4 rounded-2xl text-left hover:bg-cream/15 transition-colors"
              >
                <div className="flex gap-4">
                  {/* Thumbnail */}
                  {manifestation.thumbnailUrl ? (
                    <img
                      src={manifestation.thumbnailUrl}
                      alt=""
                      className="w-16 h-16 rounded-xl object-cover flex-shrink-0"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-xl bg-love-dark/30 flex items-center justify-center flex-shrink-0">
                      <svg className="w-6 h-6 text-cream/30" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                      </svg>
                    </div>
                  )}

                  <div className="flex-1 min-w-0">
                    {/* Status badge */}
                    <div className="mb-1">
                      {getStatusBadge(manifestation.status)}
                    </div>

                    {/* Purpose */}
                    <p className="font-medium text-cream line-clamp-1">
                      {getPurposeLabel(manifestation.purpose)}
                    </p>

                    {/* Recipient or personal */}
                    <p className="text-sm text-cream/50">
                      {manifestation.recipientName
                        ? `${t('dashboard.for')} ${manifestation.recipientName}`
                        : t('dashboard.forMe')}
                    </p>
                  </div>

                  {/* Arrow */}
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-cream/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </main>

      {/* FAB - Create new */}
      <button
        onClick={() => { playClick(); navigate('/create'); }}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full btn-love flex items-center justify-center shadow-lg hover:scale-105 transition-transform z-20"
      >
        <svg className="w-6 h-6 text-cream" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>
  );
}
