/**
 * H3 — Store Pinia pour le Diff & Validation
 * ==========================================
 * 
 * Gère :
 * - L'état des diffs chargés
 * - Les sélections et filtres utilisateur
 * - Les décisions en cours
 * - La communication avec le backend
 * 
 * Usage:
 *   const store = useDiffStore()
 *   await store.loadDiff(diffId)
 *   store.acceptObject(diffObjectId)
 *   await store.applyDiff()
 */

import { defineStore } from 'pinia';
import { ref, computed, reactive } from 'vue';
import type {
  DiffGlobal,
  DiffObject,
  Decision,
  DecisionRequest,
  UserOverride,
  ApplyDiffResult,
  DiffFilters,
  GroupBy,
  Operation,
  BundleType,
} from '../types/diff';


// =============================================================================
// TYPES INTERNES
// =============================================================================

interface DiffState {
  currentDiff: DiffGlobal | null;
  pendingDiffs: DiffGlobal[];
  selectedObjectId: string | null;
  filters: DiffFilters;
  groupBy: GroupBy;
  isLoading: boolean;
  error: string | null;
}


// =============================================================================
// API CLIENT (À ADAPTER SELON L'IMPLÉMENTATION RÉELLE)
// =============================================================================

/**
 * Client API pour le DiffService.
 * TODO: Adapter les URLs selon votre configuration backend.
 */
const API_BASE = '/api/cockpit/diffs';

async function apiGet<T>(url: string): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`);
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function apiPost<T>(url: string, data: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}


// =============================================================================
// STORE
// =============================================================================

export const useDiffStore = defineStore('diff', () => {
  // ---------------------------------------------------------------------------
  // STATE
  // ---------------------------------------------------------------------------
  
  const currentDiff = ref<DiffGlobal | null>(null);
  const pendingDiffs = ref<DiffGlobal[]>([]);
  const selectedObjectId = ref<string | null>(null);
  const filters = reactive<DiffFilters>({});
  const groupBy = ref<GroupBy>('operation');
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  
  // Décisions locales (avant soumission)
  const localDecisions = ref<Map<string, DecisionRequest>>(new Map());
  
  
  // ---------------------------------------------------------------------------
  // GETTERS
  // ---------------------------------------------------------------------------
  
  /**
   * Objet actuellement sélectionné.
   */
  const selectedObject = computed((): DiffObject | null => {
    if (!currentDiff.value || !selectedObjectId.value) return null;
    return currentDiff.value.objects.find(
      o => o.diff_object_id === selectedObjectId.value
    ) ?? null;
  });
  
  /**
   * Objets filtrés selon les critères actifs.
   */
  const filteredObjects = computed((): DiffObject[] => {
    if (!currentDiff.value) return [];
    
    let objects = currentDiff.value.objects;
    
    // Filtre par opération
    if (filters.operation?.length) {
      objects = objects.filter(o => filters.operation!.includes(o.operation));
    }
    
    // Filtre par décision
    if (filters.decision?.length) {
      objects = objects.filter(o => filters.decision!.includes(o.decision));
    }
    
    // Filtre par recherche textuelle
    if (filters.search) {
      const search = filters.search.toLowerCase();
      objects = objects.filter(o =>
        o.object_id.toLowerCase().includes(search) ||
        o.object_path.toLowerCase().includes(search) ||
        o.object_type.toLowerCase().includes(search) ||
        (o.object_label?.toLowerCase().includes(search) ?? false)
      );
    }
    
    return objects;
  });
  
  /**
   * Objets groupés selon le critère actif.
   */
  const groupedObjects = computed(() => {
    const objects = filteredObjects.value;
    
    if (groupBy.value === 'none') {
      return { ungrouped: objects };
    }
    
    const groups: Record<string, DiffObject[]> = {};
    
    for (const obj of objects) {
      let key: string;
      switch (groupBy.value) {
        case 'operation':
          key = obj.operation;
          break;
        case 'type':
          key = obj.object_type;
          break;
        case 'decision':
          key = obj.decision;
          break;
        default:
          key = 'other';
      }
      
      if (!groups[key]) groups[key] = [];
      groups[key].push(obj);
    }
    
    return groups;
  });
  
  /**
   * Nombre d'objets en attente de décision.
   */
  const pendingCount = computed((): number => {
    return currentDiff.value?.summary.pending_count ?? 0;
  });
  
  /**
   * Indique si toutes les décisions ont été prises.
   */
  const allDecided = computed((): boolean => {
    return pendingCount.value === 0 && (currentDiff.value?.objects.length ?? 0) > 0;
  });
  
  /**
   * Indique s'il y a des objets à appliquer.
   */
  const hasObjectsToApply = computed((): boolean => {
    if (!currentDiff.value) return false;
    return currentDiff.value.objects.some(
      o => o.decision === 'accepted' || o.decision === 'modified'
    );
  });
  
  /**
   * Indique si des changements locaux n'ont pas été soumis.
   */
  const hasUnsavedChanges = computed((): boolean => {
    return localDecisions.value.size > 0;
  });
  
  
  // ---------------------------------------------------------------------------
  // ACTIONS — CHARGEMENT
  // ---------------------------------------------------------------------------
  
  /**
   * Charge la liste des diffs en attente.
   */
  async function loadPendingDiffs(): Promise<void> {
    isLoading.value = true;
    error.value = null;
    
    try {
      pendingDiffs.value = await apiGet<DiffGlobal[]>('');
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur de chargement';
      throw e;
    } finally {
      isLoading.value = false;
    }
  }
  
  /**
   * Charge un diff spécifique.
   */
  async function loadDiff(diffId: string): Promise<void> {
    isLoading.value = true;
    error.value = null;
    localDecisions.value.clear();
    
    try {
      currentDiff.value = await apiGet<DiffGlobal>(`/${diffId}`);
      
      // Sélectionner le premier objet par défaut
      if (currentDiff.value.objects.length > 0 && !selectedObjectId.value) {
        selectedObjectId.value = currentDiff.value.objects[0].diff_object_id;
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur de chargement';
      throw e;
    } finally {
      isLoading.value = false;
    }
  }
  
  /**
   * Rafraîchit le diff courant.
   */
  async function refreshCurrentDiff(): Promise<void> {
    if (currentDiff.value) {
      await loadDiff(currentDiff.value.diff_id);
    }
  }
  
  
  // ---------------------------------------------------------------------------
  // ACTIONS — SÉLECTION ET FILTRES
  // ---------------------------------------------------------------------------
  
  /**
   * Sélectionne un objet pour afficher ses détails.
   */
  function selectObject(diffObjectId: string | null): void {
    selectedObjectId.value = diffObjectId;
  }
  
  /**
   * Met à jour les filtres.
   */
  function setFilters(newFilters: Partial<DiffFilters>): void {
    Object.assign(filters, newFilters);
  }
  
  /**
   * Réinitialise les filtres.
   */
  function clearFilters(): void {
    filters.operation = undefined;
    filters.decision = undefined;
    filters.bundle_type = undefined;
    filters.search = undefined;
  }
  
  /**
   * Change le mode de regroupement.
   */
  function setGroupBy(mode: GroupBy): void {
    groupBy.value = mode;
  }
  
  
  // ---------------------------------------------------------------------------
  // ACTIONS — DÉCISIONS LOCALES
  // ---------------------------------------------------------------------------
  
  /**
   * Enregistre une décision locale (avant soumission).
   */
  function setLocalDecision(
    diffObjectId: string,
    decision: Decision,
    overrides?: UserOverride[],
    comment?: string
  ): void {
    // Mettre à jour localement l'objet
    if (currentDiff.value) {
      const obj = currentDiff.value.objects.find(
        o => o.diff_object_id === diffObjectId
      );
      if (obj) {
        obj.decision = decision;
        obj.user_overrides = overrides ?? [];
        obj.user_comment = comment;
      }
      
      // Recalculer le summary
      recalculateSummary();
    }
    
    // Enregistrer pour soumission
    localDecisions.value.set(diffObjectId, {
      diff_object_id: diffObjectId,
      decision,
      overrides,
      comment,
    });
  }
  
  /**
   * Accepte un objet.
   */
  function acceptObject(diffObjectId: string, comment?: string): void {
    setLocalDecision(diffObjectId, 'accepted', undefined, comment);
  }
  
  /**
   * Rejette un objet.
   */
  function rejectObject(diffObjectId: string, comment?: string): void {
    setLocalDecision(diffObjectId, 'rejected', undefined, comment);
  }
  
  /**
   * Modifie un objet avec des overrides.
   */
  function modifyObject(
    diffObjectId: string,
    overrides: UserOverride[],
    comment?: string
  ): void {
    setLocalDecision(diffObjectId, 'modified', overrides, comment);
  }
  
  /**
   * Réinitialise la décision d'un objet.
   */
  function resetObjectDecision(diffObjectId: string): void {
    setLocalDecision(diffObjectId, 'pending');
    localDecisions.value.delete(diffObjectId);
  }
  
  /**
   * Accepte tous les objets pending.
   */
  function acceptAllPending(): void {
    if (!currentDiff.value) return;
    
    for (const obj of currentDiff.value.objects) {
      if (obj.decision === 'pending') {
        acceptObject(obj.diff_object_id);
      }
    }
  }
  
  /**
   * Rejette tous les objets pending.
   */
  function rejectAllPending(): void {
    if (!currentDiff.value) return;
    
    for (const obj of currentDiff.value.objects) {
      if (obj.decision === 'pending') {
        rejectObject(obj.diff_object_id);
      }
    }
  }
  
  /**
   * Réinitialise toutes les décisions.
   */
  function resetAllDecisions(): void {
    if (!currentDiff.value) return;
    
    for (const obj of currentDiff.value.objects) {
      obj.decision = 'pending';
      obj.user_overrides = [];
      obj.user_comment = undefined;
    }
    
    localDecisions.value.clear();
    recalculateSummary();
  }
  
  /**
   * Recalcule le summary du diff courant.
   */
  function recalculateSummary(): void {
    if (!currentDiff.value) return;
    
    const objects = currentDiff.value.objects;
    currentDiff.value.summary = {
      total_objects: objects.length,
      created_count: objects.filter(o => o.operation === 'create').length,
      updated_count: objects.filter(o => o.operation === 'update').length,
      deleted_count: objects.filter(o => o.operation === 'delete').length,
      disabled_count: objects.filter(o => o.operation === 'disable').length,
      pending_count: objects.filter(o => o.decision === 'pending').length,
      accepted_count: objects.filter(o => o.decision === 'accepted').length,
      rejected_count: objects.filter(o => o.decision === 'rejected').length,
      modified_count: objects.filter(o => o.decision === 'modified').length,
    };
  }
  
  
  // ---------------------------------------------------------------------------
  // ACTIONS — COMMUNICATION BACKEND
  // ---------------------------------------------------------------------------
  
  /**
   * Soumet les décisions locales au backend.
   */
  async function submitDecisions(userId: string): Promise<void> {
    if (!currentDiff.value || localDecisions.value.size === 0) return;
    
    isLoading.value = true;
    error.value = null;
    
    try {
      const decisions = Array.from(localDecisions.value.values());
      
      await apiPost(`/${currentDiff.value.diff_id}/decide`, {
        diff_id: currentDiff.value.diff_id,
        decisions,
        user_id: userId,
      });
      
      // Vider les décisions locales
      localDecisions.value.clear();
      
      // Rafraîchir depuis le backend
      await refreshCurrentDiff();
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur de soumission';
      throw e;
    } finally {
      isLoading.value = false;
    }
  }
  
  /**
   * Applique le diff validé.
   */
  async function applyDiff(userId: string, dryRun = false): Promise<ApplyDiffResult> {
    if (!currentDiff.value) {
      throw new Error('Aucun diff chargé');
    }
    
    // Soumettre d'abord les décisions locales si nécessaire
    if (localDecisions.value.size > 0) {
      await submitDecisions(userId);
    }
    
    isLoading.value = true;
    error.value = null;
    
    try {
      const result = await apiPost<ApplyDiffResult>(
        `/${currentDiff.value.diff_id}/apply`,
        {
          diff_id: currentDiff.value.diff_id,
          user_id: userId,
          dry_run: dryRun,
        }
      );
      
      if (!dryRun) {
        // Rafraîchir le diff pour voir le nouveau statut
        await refreshCurrentDiff();
      }
      
      return result;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur d\'application';
      throw e;
    } finally {
      isLoading.value = false;
    }
  }
  
  /**
   * Prévisualise l'application (dry run).
   */
  async function previewApply(userId: string): Promise<ApplyDiffResult> {
    return applyDiff(userId, true);
  }
  
  
  // ---------------------------------------------------------------------------
  // RESET
  // ---------------------------------------------------------------------------
  
  /**
   * Réinitialise tout le store.
   */
  function $reset(): void {
    currentDiff.value = null;
    pendingDiffs.value = [];
    selectedObjectId.value = null;
    clearFilters();
    groupBy.value = 'operation';
    isLoading.value = false;
    error.value = null;
    localDecisions.value.clear();
  }
  
  
  // ---------------------------------------------------------------------------
  // EXPORT
  // ---------------------------------------------------------------------------
  
  return {
    // State
    currentDiff,
    pendingDiffs,
    selectedObjectId,
    filters,
    groupBy,
    isLoading,
    error,
    
    // Getters
    selectedObject,
    filteredObjects,
    groupedObjects,
    pendingCount,
    allDecided,
    hasObjectsToApply,
    hasUnsavedChanges,
    
    // Actions — Chargement
    loadPendingDiffs,
    loadDiff,
    refreshCurrentDiff,
    
    // Actions — Sélection
    selectObject,
    setFilters,
    clearFilters,
    setGroupBy,
    
    // Actions — Décisions
    setLocalDecision,
    acceptObject,
    rejectObject,
    modifyObject,
    resetObjectDecision,
    acceptAllPending,
    rejectAllPending,
    resetAllDecisions,
    
    // Actions — Backend
    submitDecisions,
    applyDiff,
    previewApply,
    
    // Reset
    $reset,
  };
});


// =============================================================================
// TYPE EXPORT
// =============================================================================

export type DiffStore = ReturnType<typeof useDiffStore>;
