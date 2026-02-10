/**
 * EUREKAI C1/1 — Composant Cockpit Lineages Assistés
 * ===================================================
 * Affiche les suggestions de parents pour un objet sélectionné.
 */

import React, { useState, useMemo } from 'react';

// Types
interface SuggestionResult {
  parentId: string;
  score: number;
  scorePercent: number;
  reason: string;
  details: Record<string, number>;
}

interface FractalObject {
  id: string;
  name: string;
  lineage: string;
  parentId: string | null;
  depth: number;
  objectType: string;
  tags: string[];
}

// Données de démonstration
const DEMO_STORE: Record<string, FractalObject> = {
  core: { id: "core", name: "Core", lineage: "Core", parentId: null, depth: 1, objectType: "I", tags: ["root"] },
  core_agent: { id: "core_agent", name: "Agent", lineage: "Core:Agent", parentId: "core", depth: 2, objectType: "I", tags: ["agent"] },
  core_agent_llm: { id: "core_agent_llm", name: "LLM", lineage: "Core:Agent:LLM", parentId: "core_agent", depth: 3, objectType: "I", tags: ["ai"] },
  agency: { id: "agency", name: "Agency", lineage: "Agency", parentId: null, depth: 1, objectType: "C", tags: ["root"] },
  agency_project: { id: "agency_project", name: "Project", lineage: "Agency:Project", parentId: "agency", depth: 2, objectType: "C", tags: ["project"] },
};

const DEMO_ORPHAN: FractalObject = {
  id: "new_gpt",
  name: "GPT-4",
  lineage: "Core:Agent:LLM:GPT",
  parentId: null,
  depth: 4,
  objectType: "I",
  tags: ["openai", "llm"]
};

// Simulation de l'API suggest_parents
function suggestParents(objectId: string, store: Record<string, FractalObject>): SuggestionResult[] {
  const target = store[objectId];
  if (!target) return [];
  
  const targetSegments = target.lineage.split(':');
  const results: SuggestionResult[] = [];
  
  Object.values(store).forEach(candidate => {
    if (candidate.id === objectId) return;
    
    const candSegments = candidate.lineage.split(':');
    if (candSegments.length >= targetSegments.length) return;
    
    // Score simple basé sur les segments communs
    let matches = 0;
    candSegments.forEach((seg, i) => {
      if (targetSegments[i]?.toLowerCase() === seg.toLowerCase()) matches++;
    });
    
    if (matches === 0) return;
    
    const patternScore = matches / candSegments.length;
    const structuralScore = candSegments.length === targetSegments.length - 1 ? 1.0 : 0.5;
    const combinedScore = patternScore * 0.6 + structuralScore * 0.4;
    
    if (combinedScore > 0.3) {
      results.push({
        parentId: candidate.id,
        score: combinedScore,
        scorePercent: Math.round(combinedScore * 100),
        reason: matches === candSegments.length 
          ? `Parent direct: ${candidate.lineage}` 
          : `${matches} segments communs`,
        details: { pattern: patternScore, structural: structuralScore }
      });
    }
  });
  
  return results.sort((a, b) => b.score - a.score).slice(0, 5);
}

// Composant Badge de confiance
function ConfidenceBadge({ score }: { score: number }) {
  const color = score > 0.7 ? 'bg-green-500' : score > 0.4 ? 'bg-yellow-500' : 'bg-red-500';
  const label = score > 0.7 ? 'Haute' : score > 0.4 ? 'Moyenne' : 'Faible';
  
  return (
    <span className={`${color} text-white text-xs px-2 py-0.5 rounded-full`}>
      {label}
    </span>
  );
}

// Composant principal
export default function LineageSuggesterPanel() {
  const [selectedObject, setSelectedObject] = useState<FractalObject | null>(null);
  const [store, setStore] = useState(DEMO_STORE);
  const [pendingParent, setPendingParent] = useState<string | null>(null);
  
  // Ajouter l'orphelin au store pour la démo
  const fullStore = useMemo(() => ({
    ...store,
    [DEMO_ORPHAN.id]: DEMO_ORPHAN
  }), [store]);
  
  const suggestions = useMemo(() => {
    if (!selectedObject) return [];
    return suggestParents(selectedObject.id, fullStore);
  }, [selectedObject, fullStore]);
  
  const handleSelectOrphan = () => {
    setSelectedObject(DEMO_ORPHAN);
    setPendingParent(null);
  };
  
  const handleApplyParent = (parentId: string) => {
    setPendingParent(parentId);
  };
  
  const handleConfirm = () => {
    if (selectedObject && pendingParent) {
      // Simuler l'application du parent
      alert(`✅ Parent "${store[pendingParent]?.name}" appliqué à "${selectedObject.name}"`);
      setPendingParent(null);
      setSelectedObject(null);
    }
  };
  
  return (
    <div className="min-h-screen bg-slate-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-cyan-400 mb-2">
            🔗 EUREKAI — Lineages Assistés
          </h1>
          <p className="text-slate-400">
            C1/1 — Suggestions d'héritage pour objets orphelins
          </p>
        </div>
        
        {/* Sélection d'objet */}
        <div className="bg-slate-800 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4 text-slate-200">
            📦 Objets orphelins détectés
          </h2>
          
          <button
            onClick={handleSelectOrphan}
            className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
              selectedObject?.id === DEMO_ORPHAN.id 
                ? 'border-cyan-500 bg-cyan-500/10' 
                : 'border-slate-600 hover:border-slate-500 bg-slate-700'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-white">{DEMO_ORPHAN.name}</div>
                <div className="text-sm text-slate-400 font-mono">{DEMO_ORPHAN.lineage}</div>
              </div>
              <span className="bg-orange-500/20 text-orange-400 text-xs px-3 py-1 rounded-full">
                ⚠️ Orphelin
              </span>
            </div>
          </button>
        </div>
        
        {/* Panel de suggestions */}
        {selectedObject && (
          <div className="bg-slate-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-slate-200">
                💡 Suggestions de parents
              </h2>
              <span className="text-sm text-slate-400">
                {suggestions.length} suggestion{suggestions.length > 1 ? 's' : ''}
              </span>
            </div>
            
            {suggestions.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <div className="text-4xl mb-2">🤷</div>
                <p>Aucune suggestion disponible</p>
                <p className="text-sm">Le lineage ne correspond à aucun pattern connu</p>
              </div>
            ) : (
              <div className="space-y-3">
                {suggestions.map((suggestion, index) => {
                  const parent = fullStore[suggestion.parentId];
                  const isSelected = pendingParent === suggestion.parentId;
                  
                  return (
                    <div
                      key={suggestion.parentId}
                      onClick={() => handleApplyParent(suggestion.parentId)}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        isSelected 
                          ? 'border-green-500 bg-green-500/10' 
                          : 'border-slate-600 hover:border-slate-500 bg-slate-700/50'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-slate-500 font-mono">#{index + 1}</span>
                            <span className="font-semibold text-white">{parent?.name}</span>
                            <ConfidenceBadge score={suggestion.score} />
                          </div>
                          <div className="text-sm font-mono text-slate-400 mb-2">
                            {parent?.lineage}
                          </div>
                          <div className="text-sm text-slate-300">
                            📝 {suggestion.reason}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-cyan-400">
                            {suggestion.scorePercent}%
                          </div>
                          <div className="text-xs text-slate-500">confiance</div>
                        </div>
                      </div>
                      
                      {/* Détails des scores */}
                      <div className="mt-3 pt-3 border-t border-slate-600/50 flex gap-4 text-xs text-slate-500">
                        {Object.entries(suggestion.details).map(([key, value]) => (
                          <span key={key}>
                            {key}: <span className="text-slate-400">{Math.round(value * 100)}%</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            
            {/* Actions */}
            {pendingParent && (
              <div className="mt-6 pt-6 border-t border-slate-600 flex items-center justify-between">
                <div className="text-sm text-slate-400">
                  Parent sélectionné: <span className="text-white font-medium">
                    {fullStore[pendingParent]?.name}
                  </span>
                </div>
                <div className="flex gap-3">
                  <button 
                    onClick={() => setPendingParent(null)}
                    className="px-4 py-2 rounded-lg border border-slate-500 text-slate-300 hover:bg-slate-700"
                  >
                    Annuler
                  </button>
                  <button 
                    onClick={handleConfirm}
                    className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-500"
                  >
                    ✓ Appliquer ce parent
                  </button>
                </div>
              </div>
            )}
            
            {/* Note d'information */}
            <div className="mt-6 p-4 bg-slate-700/30 rounded-lg text-sm text-slate-400">
              <div className="flex items-start gap-2">
                <span className="text-blue-400">ℹ️</span>
                <div>
                  <strong className="text-slate-300">Note:</strong> Ces suggestions sont indicatives 
                  et basées sur l'analyse des patterns de lineage. La décision finale reste humaine.
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
