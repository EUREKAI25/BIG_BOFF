import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams, Link } from 'react-router-dom';
import Logo from '../components/Logo';
import FloatingHearts from '../components/FloatingHearts';
import { useClickSound } from '../hooks/useClickSound';

type Category = 'romantic' | 'passionate' | 'tender' | 'playful' | 'poetic';
type Purpose = 'manifest' | 'seduce' | 'love';
type Mode = 'write' | 'auto' | null;

const categories: Category[] = ['romantic', 'passionate', 'tender', 'playful', 'poetic'];
const purposes: Purpose[] = ['manifest', 'seduce', 'love'];

export default function CreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { parentGiftId } = useParams();
  const playClick = useClickSound();

  const [mode, setMode] = useState<Mode>(null);
  const [scenario, setScenario] = useState('');
  const [indication, setIndication] = useState('');
  const [purpose, setPurpose] = useState<Purpose>('manifest');
  const [category, setCategory] = useState<Category>('romantic');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (mode === 'write' && !scenario.trim()) return;
    if (mode === 'auto' && !indication.trim()) return;

    setIsGenerating(true);

    // TODO: API call to create manifestation
    await new Promise((resolve) => setTimeout(resolve, 3000));

    navigate('/preview/demo-123');
  };

  // Mode selection screen
  if (!mode) {
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
          <p className="text-cream/60 text-center mb-10">
            {t('create.chooseMode')}
          </p>

          <div className="w-full max-w-sm space-y-4">
            {/* Mode: Write scenario */}
            <button
              onClick={() => { playClick(); setMode('write'); }}
              className="btn-love w-full p-5 rounded-3xl text-left"
            >
              <p className="text-cream font-semibold text-base mb-0.5">
                {t('create.modeWrite')}
              </p>
              <p className="text-cream/60 text-sm">
                {t('create.modeWriteDesc')}
              </p>
            </button>

            {/* Mode: Auto */}
            <button
              onClick={() => { playClick(); setMode('auto'); }}
              className="btn-love w-full p-5 rounded-3xl text-left"
            >
              <p className="text-cream font-semibold text-base mb-0.5">
                {t('create.modeAuto')}
              </p>
              <p className="text-cream/60 text-sm">
                {t('create.modeAutoDesc')}
              </p>
            </button>
          </div>

          {/* Explanation */}
          <p className="text-cream/40 text-xs text-center mt-10 max-w-xs">
            {t('app.explanation')}
          </p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute inset-0 bg-love-primary" />
      <FloatingHearts count={8} />

      <header className="relative z-10 p-4 flex items-center justify-between">
        <button
          onClick={() => setMode(null)}
          className="text-cream/60 hover:text-cream transition-colors"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <Logo className="h-16" />
        <div className="w-6" />
      </header>

      <main className="relative z-10 flex-1 px-6 py-4 overflow-y-auto">
        <div className="max-w-md mx-auto">
          {parentGiftId && (
            <div className="glass-love-light p-4 rounded-xl mb-6 text-center">
              <p className="text-cream/80 text-sm">
                Vous répondez à une manifestation reçue
              </p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Purpose */}
            <div>
              <label className="block text-cream/80 text-sm mb-3">
                {t('create.purpose')}
              </label>
              <div className="space-y-2">
                {purposes.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => { playClick(); setPurpose(p); }}
                    className={`w-full text-left text-sm ${
                      purpose === p
                        ? 'option-love-selected'
                        : 'option-love'
                    }`}
                  >
                    {t(`create.purposes.${p}`)}
                  </button>
                ))}
              </div>
            </div>

            {/* Scenario or Indication based on mode */}
            {mode === 'write' ? (
              <div>
                <label className="block text-cream/80 text-sm mb-2">
                  {t('create.scenario')}
                </label>
                <textarea
                  value={scenario}
                  onChange={(e) => setScenario(e.target.value)}
                  placeholder={t('create.scenarioPlaceholder')}
                  rows={6}
                  className="input-love resize-none"
                  required
                />
              </div>
            ) : (
              <div>
                <label className="block text-cream/80 text-sm mb-2">
                  {t('create.indication')}
                </label>
                <textarea
                  value={indication}
                  onChange={(e) => setIndication(e.target.value)}
                  placeholder={t('create.indicationPlaceholder')}
                  rows={6}
                  className="input-love resize-none"
                  required
                />
              </div>
            )}

            {/* Category */}
            <div>
              <label className="block text-cream/80 text-sm mb-3">
                {t('create.category')}
              </label>
              <div className="flex flex-wrap gap-2">
                {categories.map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => { playClick(); setCategory(cat); }}
                    className={`text-sm ${
                      category === cat
                        ? 'option-love-selected'
                        : 'option-love'
                    }`}
                  >
                    {t(`create.categories.${cat}`)}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isGenerating || (mode === 'write' ? !scenario.trim() : !indication.trim())}
              className="btn-love w-full py-3 text-base disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGenerating ? (
                <span className="flex items-center justify-center gap-3">
                  <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  {t('create.generating')}
                </span>
              ) : (
                t('create.generateButton')
              )}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
