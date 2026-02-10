<template>
  <div class="diff-validation-view">
    <!-- Header global -->
    <header class="view-header">
      <div class="view-header__left">
        <h1>Validation des changements</h1>
        <div v-if="currentDiff" class="view-header__info">
          <span class="scenario-name">{{ currentDiff.scenario_name || currentDiff.scenario_id }}</span>
          <span class="status-badge" :class="`status-badge--${currentDiff.status}`">
            {{ formatStatus(currentDiff.status) }}
          </span>
        </div>
      </div>
      
      <div class="view-header__right">
        <!-- Sélecteur de diff -->
        <select 
          v-if="pendingDiffs.length > 0"
          v-model="selectedDiffId"
          class="diff-select"
          @change="onDiffSelect"
        >
          <option value="">Sélectionner un diff...</option>
          <option 
            v-for="diff in pendingDiffs" 
            :key="diff.diff_id"
            :value="diff.diff_id"
          >
            {{ diff.scenario_name || diff.scenario_id }} 
            ({{ diff.summary.total_objects }} objets)
          </option>
        </select>
        
        <!-- Bouton d'application -->
        <button
          v-if="currentDiff && hasObjectsToApply"
          class="btn btn--primary"
          :disabled="isLoading"
          @click="openApplyModal"
        >
          Appliquer ({{ applyCount }})
        </button>
      </div>
    </header>
    
    <!-- Résumé -->
    <div v-if="currentDiff" class="view-summary">
      <div class="summary-card">
        <span class="summary-card__value">{{ currentDiff.summary.total_objects }}</span>
        <span class="summary-card__label">Total</span>
      </div>
      <div class="summary-card summary-card--create">
        <span class="summary-card__value">{{ currentDiff.summary.created_count }}</span>
        <span class="summary-card__label">Créations</span>
      </div>
      <div class="summary-card summary-card--update">
        <span class="summary-card__value">{{ currentDiff.summary.updated_count }}</span>
        <span class="summary-card__label">Modifications</span>
      </div>
      <div class="summary-card summary-card--delete">
        <span class="summary-card__value">{{ currentDiff.summary.deleted_count }}</span>
        <span class="summary-card__label">Suppressions</span>
      </div>
      <div class="summary-card summary-card--pending">
        <span class="summary-card__value">{{ currentDiff.summary.pending_count }}</span>
        <span class="summary-card__label">En attente</span>
      </div>
      <div class="summary-card summary-card--accepted">
        <span class="summary-card__value">{{ currentDiff.summary.accepted_count }}</span>
        <span class="summary-card__label">Acceptés</span>
      </div>
      <div class="summary-card summary-card--rejected">
        <span class="summary-card__value">{{ currentDiff.summary.rejected_count }}</span>
        <span class="summary-card__label">Refusés</span>
      </div>
    </div>
    
    <!-- Contenu principal -->
    <div class="view-content">
      <!-- État de chargement -->
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Chargement...</p>
      </div>
      
      <!-- Erreur -->
      <div v-else-if="error" class="error-state">
        <p>❌ {{ error }}</p>
        <button class="btn btn--secondary" @click="retry">Réessayer</button>
      </div>
      
      <!-- État vide -->
      <div v-else-if="!currentDiff" class="empty-state">
        <p>Aucun diff sélectionné.</p>
        <p v-if="pendingDiffs.length === 0">
          Aucun diff en attente de validation.
        </p>
      </div>
      
      <!-- Vue split liste/détail -->
      <template v-else>
        <div class="split-view">
          <!-- Liste des objets -->
          <div class="split-view__list">
            <DiffList
              :objects="currentDiff.objects"
              :selected-id="selectedObjectId"
              :group-by="groupBy"
              @select="selectObject"
              @accept-all="acceptAllPending"
              @reject-all="rejectAllPending"
              @reset-all="resetAllDecisions"
              @filter-change="onFilterChange"
              @group-by-change="setGroupBy"
            />
          </div>
          
          <!-- Détail de l'objet sélectionné -->
          <div class="split-view__detail">
            <DiffDetail
              :object="selectedObject"
              @accept="acceptObject"
              @reject="rejectObject"
              @modify="modifyObject"
              @reset="resetObjectDecision"
            />
          </div>
        </div>
      </template>
    </div>
    
    <!-- Modal de confirmation d'application -->
    <ConfirmationModal
      :visible="showApplyModal"
      title="Appliquer les changements"
      message="Vous êtes sur le point d'appliquer les changements validés à la fractale."
      :summary="currentDiff?.summary"
      :warnings="applyWarnings"
      :preview-result="previewResult"
      confirm-label="Appliquer"
      confirm-button-class="btn--primary"
      :require-confirmation="true"
      confirm-text="APPLIQUER"
      @confirm="confirmApply"
      @cancel="closeApplyModal"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useDiffStore } from '../stores/diffStore';
import type { DiffFilters, GroupBy, UserOverride, ApplyDiffResult } from '../types/diff';
import { formatStatus } from '../types/diff';
import DiffList from '../components/DiffList.vue';
import DiffDetail from '../components/DiffDetail.vue';
import ConfirmationModal from '../components/ConfirmationModal.vue';

// Store
const store = useDiffStore();

// État local
const selectedDiffId = ref('');
const showApplyModal = ref(false);
const previewResult = ref<ApplyDiffResult | null>(null);

// TODO: Récupérer l'ID utilisateur depuis le contexte d'authentification
const currentUserId = 'user-cockpit';

// Computed depuis le store
const currentDiff = computed(() => store.currentDiff);
const pendingDiffs = computed(() => store.pendingDiffs);
const selectedObjectId = computed(() => store.selectedObjectId);
const selectedObject = computed(() => store.selectedObject);
const groupBy = computed(() => store.groupBy);
const isLoading = computed(() => store.isLoading);
const error = computed(() => store.error);
const hasObjectsToApply = computed(() => store.hasObjectsToApply);

const applyCount = computed(() => {
  if (!currentDiff.value) return 0;
  return currentDiff.value.summary.accepted_count + currentDiff.value.summary.modified_count;
});

const applyWarnings = computed(() => {
  const warnings: string[] = [];
  if (currentDiff.value) {
    if (currentDiff.value.summary.pending_count > 0) {
      warnings.push(`${currentDiff.value.summary.pending_count} objet(s) sans décision seront ignorés.`);
    }
    if (currentDiff.value.summary.rejected_count > 0) {
      warnings.push(`${currentDiff.value.summary.rejected_count} objet(s) refusés ne seront pas appliqués.`);
    }
  }
  return warnings;
});

// Lifecycle
onMounted(async () => {
  await store.loadPendingDiffs();
  
  // Charger le premier diff s'il existe
  if (pendingDiffs.value.length > 0) {
    selectedDiffId.value = pendingDiffs.value[0].diff_id;
    await store.loadDiff(selectedDiffId.value);
  }
});

// Watch pour sync du select
watch(selectedDiffId, async (newId) => {
  if (newId && newId !== currentDiff.value?.diff_id) {
    await store.loadDiff(newId);
  }
});

// Handlers
function selectObject(id: string): void {
  store.selectObject(id);
}

function acceptObject(id: string): void {
  store.acceptObject(id);
}

function rejectObject(id: string): void {
  store.rejectObject(id);
}

function modifyObject(id: string, overrides: UserOverride[], comment?: string): void {
  store.modifyObject(id, overrides, comment);
}

function resetObjectDecision(id: string): void {
  store.resetObjectDecision(id);
}

function acceptAllPending(): void {
  store.acceptAllPending();
}

function rejectAllPending(): void {
  store.rejectAllPending();
}

function resetAllDecisions(): void {
  store.resetAllDecisions();
}

function onFilterChange(filters: Partial<DiffFilters>): void {
  store.setFilters(filters);
}

function setGroupBy(mode: GroupBy): void {
  store.setGroupBy(mode);
}

async function onDiffSelect(): Promise<void> {
  if (selectedDiffId.value) {
    await store.loadDiff(selectedDiffId.value);
  }
}

async function retry(): Promise<void> {
  await store.loadPendingDiffs();
}

// Application
async function openApplyModal(): Promise<void> {
  // Soumettre d'abord les décisions locales
  if (store.hasUnsavedChanges) {
    await store.submitDecisions(currentUserId);
  }
  
  // Faire un preview
  try {
    previewResult.value = await store.previewApply(currentUserId);
    showApplyModal.value = true;
  } catch (e) {
    console.error('Preview failed:', e);
    showApplyModal.value = true;
  }
}

function closeApplyModal(): void {
  showApplyModal.value = false;
  previewResult.value = null;
}

async function confirmApply(): Promise<void> {
  try {
    const result = await store.applyDiff(currentUserId);
    closeApplyModal();
    
    if (result.success) {
      // Rafraîchir la liste des diffs
      await store.loadPendingDiffs();
      
      // Notification de succès (TODO: intégrer un système de toast)
      alert(`✅ Application réussie: ${result.applied_count} objet(s) appliqué(s).`);
    } else {
      alert(`⚠️ Application partielle: ${result.error_count} erreur(s).`);
    }
  } catch (e) {
    console.error('Apply failed:', e);
    alert('❌ Erreur lors de l\'application.');
  }
}
</script>

<style scoped>
.diff-validation-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f3f4f6;
}

/* Header */
.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.view-header__left h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.view-header__info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}

.scenario-name {
  font-size: 14px;
  color: #6b7280;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge--pending { background: #fef3c7; color: #92400e; }
.status-badge--partial { background: #dbeafe; color: #1e40af; }
.status-badge--validated { background: #d1fae5; color: #065f46; }
.status-badge--applied { background: #d1fae5; color: #065f46; }
.status-badge--rejected { background: #fee2e2; color: #991b1b; }
.status-badge--error { background: #fee2e2; color: #991b1b; }

.view-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.diff-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  min-width: 250px;
}

/* Résumé */
.view-summary {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  overflow-x: auto;
}

.summary-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 20px;
  background: #f9fafb;
  border-radius: 8px;
  min-width: 80px;
}

.summary-card__value {
  font-size: 24px;
  font-weight: 700;
  color: #374151;
}

.summary-card__label {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.summary-card--create { background: #ecfdf5; }
.summary-card--create .summary-card__value { color: #059669; }

.summary-card--update { background: #eff6ff; }
.summary-card--update .summary-card__value { color: #2563eb; }

.summary-card--delete { background: #fef2f2; }
.summary-card--delete .summary-card__value { color: #dc2626; }

.summary-card--pending { background: #fefce8; }
.summary-card--pending .summary-card__value { color: #ca8a04; }

.summary-card--accepted { background: #ecfdf5; }
.summary-card--accepted .summary-card__value { color: #059669; }

.summary-card--rejected { background: #fef2f2; }
.summary-card--rejected .summary-card__value { color: #dc2626; }

/* Contenu principal */
.view-content {
  flex: 1;
  overflow: hidden;
  padding: 16px 24px;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6b7280;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  color: #dc2626;
}

/* Vue split */
.split-view {
  display: flex;
  gap: 16px;
  height: 100%;
}

.split-view__list {
  width: 400px;
  flex-shrink: 0;
}

.split-view__detail {
  flex: 1;
  min-width: 0;
}

/* Boutons */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn--primary {
  background: #3b82f6;
  color: white;
}

.btn--primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn--secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 900px) {
  .split-view {
    flex-direction: column;
  }
  
  .split-view__list {
    width: 100%;
    height: 300px;
  }
}
</style>
