# CHANTIER 10 — FRONTEND (Interface Web)

⚠️ **CE PROJET N'UTILISE PAS EUREKAI**

---

## OBJECTIF
Créer l'interface web pour utiliser le service Web2App : saisie d'URL, suivi de progression, preview et téléchargement.

## PRÉREQUIS
- C09 API (endpoints disponibles)

## PAGES

```
/                   # Landing + formulaire
/convert            # Suivi de progression
/result/{job_id}    # Résultat + preview + download
```

---

## STRUCTURE

```
frontend/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── ConvertPage.tsx
│   │   └── ResultPage.tsx
│   ├── components/
│   │   ├── UrlInput.tsx
│   │   ├── ProgressTracker.tsx
│   │   ├── PreviewFrame.tsx
│   │   └── DownloadButton.tsx
│   ├── hooks/
│   │   ├── useConvert.ts
│   │   └── useJobStatus.ts
│   └── lib/
│       └── api.ts
├── package.json
└── tailwind.config.js
```

---

## PAGES

### pages/HomePage.tsx

```tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UrlInput } from '../components/UrlInput';
import { useConvert } from '../hooks/useConvert';

export function HomePage() {
  const [url, setUrl] = useState('');
  const { convert, isLoading, error } = useConvert();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await convert(url);
    if (result?.job_id) {
      navigate(`/convert?job=${result.job_id}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white">
      {/* Hero */}
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          Transformez votre site web en{' '}
          <span className="text-purple-600">app mobile</span>
        </h1>
        
        <p className="text-xl text-gray-600 mb-12">
          Entrez l'URL de votre site et obtenez un projet Expo complet
          (iOS + Android) en quelques minutes.
        </p>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="max-w-xl mx-auto">
          <UrlInput 
            value={url} 
            onChange={setUrl}
            disabled={isLoading}
          />
          
          <button
            type="submit"
            disabled={isLoading || !url}
            className="mt-4 w-full py-4 px-8 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Analyse en cours...' : 'Convertir →'}
          </button>
          
          {error && (
            <p className="mt-4 text-red-600">{error}</p>
          )}
        </form>
      </div>
      
      {/* Features */}
      <div className="max-w-5xl mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          <FeatureCard
            icon="🔍"
            title="Analyse intelligente"
            description="L'IA analyse la structure de votre site et identifie les composants."
          />
          <FeatureCard
            icon="⚡"
            title="Conversion rapide"
            description="Génération automatique du code React Native en quelques minutes."
          />
          <FeatureCard
            icon="📱"
            title="Preview instantané"
            description="Testez votre app sur iOS et Android avant de télécharger."
          />
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="p-6 bg-white rounded-xl shadow-sm border">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}
```

### pages/ConvertPage.tsx

```tsx
import { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { ProgressTracker } from '../components/ProgressTracker';
import { useJobStatus } from '../hooks/useJobStatus';

export function ConvertPage() {
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get('job');
  const navigate = useNavigate();
  
  const { status, progress, currentStep, error } = useJobStatus(jobId);

  useEffect(() => {
    if (status === 'completed') {
      navigate(`/result/${jobId}`);
    }
  }, [status, jobId, navigate]);

  if (!jobId) {
    return <div>Job ID manquant</div>;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white p-8 rounded-2xl shadow-lg">
          <h1 className="text-2xl font-bold text-center mb-8">
            Conversion en cours...
          </h1>
          
          <ProgressTracker 
            progress={progress}
            currentStep={currentStep}
            status={status}
          />
          
          {error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600">{error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

### pages/ResultPage.tsx

```tsx
import { useParams } from 'react-router-dom';
import { PreviewFrame } from '../components/PreviewFrame';
import { DownloadButton } from '../components/DownloadButton';
import { useJobResult } from '../hooks/useJobResult';

export function ResultPage() {
  const { jobId } = useParams();
  const { result, isLoading } = useJobResult(jobId);

  if (isLoading) {
    return <div>Chargement...</div>;
  }

  if (!result) {
    return <div>Résultat non trouvé</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-center mb-2">
          🎉 Votre app est prête !
        </h1>
        <p className="text-gray-600 text-center mb-12">
          {result.stats?.screens} écrans • {result.stats?.components} composants
        </p>
        
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Preview */}
          <div className="bg-white p-6 rounded-xl shadow-sm">
            <h2 className="text-xl font-semibold mb-4">Preview</h2>
            <PreviewFrame snackId={result.preview_url?.split('/').pop()} />
          </div>
          
          {/* Download */}
          <div className="bg-white p-6 rounded-xl shadow-sm">
            <h2 className="text-xl font-semibold mb-4">Télécharger</h2>
            
            <div className="space-y-4">
              <DownloadButton 
                jobId={jobId}
                label="Télécharger le projet Expo"
              />
              
              <div className="p-4 bg-gray-50 rounded-lg">
                <h3 className="font-medium mb-2">Prochaines étapes :</h3>
                <ol className="list-decimal list-inside text-gray-600 space-y-1 text-sm">
                  <li>Extraire le ZIP</li>
                  <li>Ouvrir un terminal dans le dossier</li>
                  <li>Exécuter <code className="bg-gray-200 px-1 rounded">npm install</code></li>
                  <li>Exécuter <code className="bg-gray-200 px-1 rounded">npx expo start</code></li>
                  <li>Scanner le QR code avec Expo Go</li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## COMPOSANTS

### components/ProgressTracker.tsx

```tsx
interface ProgressTrackerProps {
  progress: number;
  currentStep: string;
  status: string;
}

export function ProgressTracker({ progress, currentStep, status }: ProgressTrackerProps) {
  const steps = [
    { label: 'Analyse', threshold: 10 },
    { label: 'Composants', threshold: 30 },
    { label: 'Styles', threshold: 50 },
    { label: 'Assets', threshold: 60 },
    { label: 'Génération', threshold: 80 },
    { label: 'Finalisation', threshold: 95 },
  ];

  return (
    <div>
      {/* Barre de progression */}
      <div className="h-3 bg-gray-200 rounded-full overflow-hidden mb-4">
        <div 
          className="h-full bg-purple-600 transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
      
      {/* Étape actuelle */}
      <p className="text-center text-gray-600 mb-6">{currentStep}</p>
      
      {/* Steps */}
      <div className="flex justify-between">
        {steps.map((step, i) => (
          <div key={i} className="flex flex-col items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              progress >= step.threshold 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-200 text-gray-500'
            }`}>
              {progress >= step.threshold ? '✓' : i + 1}
            </div>
            <span className="text-xs mt-1 text-gray-500">{step.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## HOOKS

### hooks/useJobStatus.ts

```typescript
import { useState, useEffect } from 'react';
import { api } from '../lib/api';

export function useJobStatus(jobId: string | null) {
  const [status, setStatus] = useState('pending');
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const poll = async () => {
      try {
        const data = await api.getStatus(jobId);
        setStatus(data.status);
        setProgress(data.progress);
        setCurrentStep(data.current_step);
        setError(data.error);

        if (data.status !== 'completed' && data.status !== 'failed') {
          setTimeout(poll, 2000);
        }
      } catch (err) {
        setError('Erreur de connexion');
      }
    };

    poll();
  }, [jobId]);

  return { status, progress, currentStep, error };
}
```

---

## LIVRABLES

```
frontend/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── ConvertPage.tsx
│   │   └── ResultPage.tsx
│   ├── components/
│   │   ├── UrlInput.tsx
│   │   ├── ProgressTracker.tsx
│   │   ├── PreviewFrame.tsx
│   │   └── DownloadButton.tsx
│   ├── hooks/
│   │   ├── useConvert.ts
│   │   ├── useJobStatus.ts
│   │   └── useJobResult.ts
│   └── lib/
│       └── api.ts
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

## CRITÈRES DE VALIDATION

- [ ] Landing page avec formulaire URL
- [ ] Page de progression avec polling
- [ ] Page résultat avec preview
- [ ] Téléchargement du ZIP
- [ ] Responsive

## TEMPS ESTIMÉ
4 heures
