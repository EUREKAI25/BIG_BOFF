/**
 * H3 — Tests Unitaires du Store Pinia
 * ====================================
 *
 * Tests couvrant :
 * - Gestion de l'état (chargement, sélection)
 * - Décisions locales (accept/reject/modify/reset)
 * - Filtrage et groupement
 * - Communication avec le backend (mockée)
 * - Cas d'erreur et sécurité
 *
 * Exécution : npm run test (avec vitest)
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useDiffStore } from '../stores/diffStore';
import type { DiffGlobal, DiffObject, ApplyDiffResult } from '../types/diff';


// =============================================================================
// MOCKS ET FIXTURES
// =============================================================================

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Fixture : DiffObject basique
function createMockDiffObject(overrides: Partial<DiffObject> = {}): DiffObject {
  return {
    diff_object_id: `obj-${Math.random().toString(36).slice(2, 9)}`,
    object_id: 'test-obj-1',
    object_type: 'User',
    object_path: '/app/users/1',
    object_label: 'Test User',
    operation: 'create',
    decision: 'pending',
    user_overrides: [],
    ...overrides,
  };
}

// Fixture : DiffGlobal basique
function createMockDiffGlobal(overrides: Partial<DiffGlobal> = {}): DiffGlobal {
  const objects = overrides.objects ?? [
    createMockDiffObject({ diff_object_id: 'obj-1' }),
    createMockDiffObject({ diff_object_id: 'obj-2', operation: 'update' }),
    createMockDiffObject({ diff_object_id: 'obj-3', operation: 'delete' }),
  ];

  return {
    diff_id: 'diff-123',
    scenario_id: 'scenario-1',
    scenario_name: 'Test Scenario',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    status: 'pending',
    objects,
    summary: {
      total_objects: objects.length,
      created_count: objects.filter(o => o.operation === 'create').length,
      updated_count: objects.filter(o => o.operation === 'update').length,
      deleted_count: objects.filter(o => o.operation === 'delete').length,
      disabled_count: 0,
      pending_count: objects.filter(o => o.decision === 'pending').length,
      accepted_count: objects.filter(o => o.decision === 'accepted').length,
      rejected_count: objects.filter(o => o.decision === 'rejected').length,
      modified_count: objects.filter(o => o.decision === 'modified').length,
    },
    ...overrides,
  };
}

// Helper pour configurer le mock fetch
function setupFetchMock(responses: Record<string, unknown>) {
  mockFetch.mockImplementation(async (url: string, options?: RequestInit) => {
    const path = url.replace('/api/cockpit/diffs', '');
    const method = options?.method || 'GET';
    const key = `${method}:${path || '/'}`;
    
    if (responses[key]) {
      return {
        ok: true,
        json: async () => responses[key],
      };
    }
    
    // Fallback pour GET /
    if (method === 'GET' && path === '') {
      return { ok: true, json: async () => [] };
    }
    
    return { ok: false, status: 404, statusText: 'Not Found' };
  });
}


// =============================================================================
// TESTS
// =============================================================================

describe('useDiffStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ---------------------------------------------------------------------------
  // ÉTAT INITIAL
  // ---------------------------------------------------------------------------

  describe('État initial', () => {
    it('devrait avoir un état initial correct', () => {
      const store = useDiffStore();

      expect(store.currentDiff).toBeNull();
      expect(store.pendingDiffs).toEqual([]);
      expect(store.selectedObjectId).toBeNull();
      expect(store.isLoading).toBe(false);
      expect(store.error).toBeNull();
    });

    it('devrait calculer selectedObject comme null quand rien n\'est sélectionné', () => {
      const store = useDiffStore();
      expect(store.selectedObject).toBeNull();
    });
  });

  // ---------------------------------------------------------------------------
  // CHARGEMENT
  // ---------------------------------------------------------------------------

  describe('Chargement', () => {
    it('devrait charger les diffs pending', async () => {
      const mockDiffs = [createMockDiffGlobal()];
      setupFetchMock({ 'GET:/': mockDiffs });

      const store = useDiffStore();
      await store.loadPendingDiffs();

      expect(store.pendingDiffs).toEqual(mockDiffs);
      expect(store.isLoading).toBe(false);
    });

    it('devrait charger un diff spécifique', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');

      expect(store.currentDiff).toEqual(mockDiff);
      expect(store.selectedObjectId).toBe('obj-1'); // Premier objet auto-sélectionné
    });

    it('devrait gérer les erreurs de chargement', async () => {
      mockFetch.mockImplementation(async () => ({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      }));

      const store = useDiffStore();
      
      await expect(store.loadDiff('bad-id')).rejects.toThrow();
      expect(store.error).toContain('API Error');
    });
  });

  // ---------------------------------------------------------------------------
  // SÉLECTION ET FILTRES
  // ---------------------------------------------------------------------------

  describe('Sélection et filtres', () => {
    it('devrait sélectionner un objet', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.selectObject('obj-2');

      expect(store.selectedObjectId).toBe('obj-2');
      expect(store.selectedObject?.diff_object_id).toBe('obj-2');
    });

    it('devrait filtrer les objets par opération', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.setFilters({ operation: ['create'] });

      const filtered = store.filteredObjects;
      expect(filtered.every(o => o.operation === 'create')).toBe(true);
    });

    it('devrait filtrer les objets par décision', async () => {
      const objects = [
        createMockDiffObject({ diff_object_id: 'obj-1', decision: 'accepted' }),
        createMockDiffObject({ diff_object_id: 'obj-2', decision: 'pending' }),
        createMockDiffObject({ diff_object_id: 'obj-3', decision: 'rejected' }),
      ];
      const mockDiff = createMockDiffGlobal({ objects });
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.setFilters({ decision: ['pending'] });

      expect(store.filteredObjects.length).toBe(1);
      expect(store.filteredObjects[0].decision).toBe('pending');
    });

    it('devrait filtrer par recherche textuelle', async () => {
      const objects = [
        createMockDiffObject({ diff_object_id: 'obj-1', object_type: 'User' }),
        createMockDiffObject({ diff_object_id: 'obj-2', object_type: 'Product' }),
      ];
      const mockDiff = createMockDiffGlobal({ objects });
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.setFilters({ search: 'Product' });

      expect(store.filteredObjects.length).toBe(1);
      expect(store.filteredObjects[0].object_type).toBe('Product');
    });

    it('devrait effacer les filtres', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.setFilters({ operation: ['create'], search: 'test' });
      store.clearFilters();

      expect(store.filters.operation).toBeUndefined();
      expect(store.filters.search).toBeUndefined();
    });

    it('devrait grouper les objets', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.setGroupBy('operation');

      const grouped = store.groupedObjects;
      expect(grouped['create']).toBeDefined();
      expect(grouped['update']).toBeDefined();
      expect(grouped['delete']).toBeDefined();
    });
  });

  // ---------------------------------------------------------------------------
  // DÉCISIONS LOCALES
  // ---------------------------------------------------------------------------

  describe('Décisions locales', () => {
    it('devrait accepter un objet localement', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.acceptObject('obj-1', 'LGTM');

      expect(store.currentDiff?.objects[0].decision).toBe('accepted');
      expect(store.currentDiff?.objects[0].user_comment).toBe('LGTM');
      expect(store.hasUnsavedChanges).toBe(true);
    });

    it('devrait rejeter un objet localement', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.rejectObject('obj-2', 'Not approved');

      expect(store.currentDiff?.objects[1].decision).toBe('rejected');
    });

    it('devrait modifier un objet avec overrides', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      const overrides = [{
        field_path: 'attributes.name',
        original_proposed: 'Alice',
        user_value: 'Alicia',
      }];
      store.modifyObject('obj-1', overrides, 'Name changed');

      expect(store.currentDiff?.objects[0].decision).toBe('modified');
      expect(store.currentDiff?.objects[0].user_overrides).toEqual(overrides);
    });

    it('devrait réinitialiser la décision d\'un objet', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.acceptObject('obj-1');
      store.resetObjectDecision('obj-1');

      expect(store.currentDiff?.objects[0].decision).toBe('pending');
    });

    it('devrait accepter tous les objets pending', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.acceptAllPending();

      expect(store.currentDiff?.objects.every(o => o.decision === 'accepted')).toBe(true);
    });

    it('devrait rejeter tous les objets pending', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.rejectAllPending();

      expect(store.currentDiff?.objects.every(o => o.decision === 'rejected')).toBe(true);
    });

    it('devrait réinitialiser toutes les décisions', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.acceptAllPending();
      store.resetAllDecisions();

      expect(store.currentDiff?.objects.every(o => o.decision === 'pending')).toBe(true);
      expect(store.hasUnsavedChanges).toBe(false);
    });

    it('devrait mettre à jour le summary après décision', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      expect(store.currentDiff?.summary.pending_count).toBe(3);
      
      store.acceptObject('obj-1');
      store.rejectObject('obj-2');

      expect(store.currentDiff?.summary.pending_count).toBe(1);
      expect(store.currentDiff?.summary.accepted_count).toBe(1);
      expect(store.currentDiff?.summary.rejected_count).toBe(1);
    });
  });

  // ---------------------------------------------------------------------------
  // COMMUNICATION BACKEND
  // ---------------------------------------------------------------------------

  describe('Communication backend', () => {
    it('devrait soumettre les décisions locales', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({
        'GET:/diff-123': mockDiff,
        'POST:/diff-123/decide': mockDiff,
      });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.acceptObject('obj-1');
      await store.submitDecisions('user-1');

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/cockpit/diffs/diff-123/decide',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
      expect(store.hasUnsavedChanges).toBe(false);
    });

    it('devrait appliquer le diff', async () => {
      const mockDiff = createMockDiffGlobal();
      const applyResult: ApplyDiffResult = {
        diff_id: 'diff-123',
        success: true,
        applied_count: 2,
        skipped_count: 1,
        error_count: 0,
        errors: [],
      };
      
      setupFetchMock({
        'GET:/diff-123': mockDiff,
        'POST:/diff-123/apply': applyResult,
      });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      store.acceptAllPending();
      
      const result = await store.applyDiff('user-1');

      expect(result.success).toBe(true);
      expect(result.applied_count).toBe(2);
    });

    it('devrait faire un dry run (preview)', async () => {
      const mockDiff = createMockDiffGlobal();
      const previewResult: ApplyDiffResult = {
        diff_id: 'diff-123',
        success: true,
        applied_count: 3,
        skipped_count: 0,
        error_count: 0,
        errors: [],
      };
      
      setupFetchMock({
        'GET:/diff-123': mockDiff,
        'POST:/diff-123/apply': previewResult,
      });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      store.acceptAllPending();
      
      const result = await store.previewApply('user-1');

      expect(result.applied_count).toBe(3);
    });
  });

  // ---------------------------------------------------------------------------
  // GETTERS CALCULÉS
  // ---------------------------------------------------------------------------

  describe('Getters calculés', () => {
    it('devrait calculer pendingCount', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');

      expect(store.pendingCount).toBe(3);
    });

    it('devrait calculer allDecided', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');

      expect(store.allDecided).toBe(false);
      
      store.acceptAllPending();
      
      expect(store.allDecided).toBe(true);
    });

    it('devrait calculer hasObjectsToApply', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');

      expect(store.hasObjectsToApply).toBe(false);
      
      store.acceptObject('obj-1');
      
      expect(store.hasObjectsToApply).toBe(true);
    });
  });

  // ---------------------------------------------------------------------------
  // CAS DE SÉCURITÉ
  // ---------------------------------------------------------------------------

  describe('Sécurité', () => {
    it('ne devrait pas avoir d\'objets à appliquer si tout est pending', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');

      // Tout est pending par défaut
      expect(store.hasObjectsToApply).toBe(false);
    });

    it('ne devrait pas avoir d\'objets à appliquer si tout est rejeté', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.rejectAllPending();

      expect(store.hasObjectsToApply).toBe(false);
    });

    it('devrait considérer les objets MODIFIED comme applicables', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff });

      const store = useDiffStore();
      await store.loadDiff('diff-123');
      
      store.modifyObject('obj-1', [{
        field_path: 'attributes.x',
        original_proposed: 'a',
        user_value: 'b',
      }]);

      expect(store.hasObjectsToApply).toBe(true);
    });
  });

  // ---------------------------------------------------------------------------
  // RESET
  // ---------------------------------------------------------------------------

  describe('Reset', () => {
    it('devrait réinitialiser tout le store', async () => {
      const mockDiff = createMockDiffGlobal();
      setupFetchMock({ 'GET:/diff-123': mockDiff, 'GET:/': [mockDiff] });

      const store = useDiffStore();
      await store.loadPendingDiffs();
      await store.loadDiff('diff-123');
      store.acceptObject('obj-1');
      store.setFilters({ search: 'test' });

      store.$reset();

      expect(store.currentDiff).toBeNull();
      expect(store.pendingDiffs).toEqual([]);
      expect(store.selectedObjectId).toBeNull();
      expect(store.hasUnsavedChanges).toBe(false);
    });
  });
});
