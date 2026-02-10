<template>
  <Teleport to="body">
    <div v-if="visible" class="modal">
      <div class="modal__overlay" @click="$emit('cancel')"></div>
      
      <div class="modal__content">
        <!-- Header -->
        <div class="modal__header">
          <h3>{{ title }}</h3>
          <button class="modal__close" @click="$emit('cancel')">×</button>
        </div>
        
        <!-- Body -->
        <div class="modal__body">
          <p class="modal__message">{{ message }}</p>
          
          <!-- Résumé des actions -->
          <div v-if="summary" class="modal__summary">
            <h4>Résumé des actions:</h4>
            <ul>
              <li v-if="summary.accepted_count > 0" class="summary-item summary-item--accepted">
                <span class="icon">✓</span>
                {{ summary.accepted_count }} objet(s) à créer/modifier
              </li>
              <li v-if="summary.modified_count > 0" class="summary-item summary-item--modified">
                <span class="icon">✎</span>
                {{ summary.modified_count }} objet(s) avec modifications utilisateur
              </li>
              <li v-if="summary.rejected_count > 0" class="summary-item summary-item--rejected">
                <span class="icon">✗</span>
                {{ summary.rejected_count }} objet(s) refusés (ignorés)
              </li>
              <li v-if="summary.pending_count > 0" class="summary-item summary-item--pending">
                <span class="icon">?</span>
                {{ summary.pending_count }} objet(s) en attente (ignorés)
              </li>
            </ul>
          </div>
          
          <!-- Avertissements -->
          <div v-if="warnings.length > 0" class="modal__warnings">
            <div v-for="(warning, idx) in warnings" :key="idx" class="warning">
              ⚠️ {{ warning }}
            </div>
          </div>
          
          <!-- Preview (dry run) -->
          <div v-if="previewResult" class="modal__preview">
            <h4>Prévisualisation:</h4>
            <div class="preview-stats">
              <span class="stat">{{ previewResult.applied_count }} application(s)</span>
              <span class="stat">{{ previewResult.skipped_count }} ignoré(s)</span>
            </div>
          </div>
          
          <!-- Zone de confirmation -->
          <div v-if="requireConfirmation" class="modal__confirm-input">
            <label>Tapez <strong>{{ confirmText }}</strong> pour confirmer:</label>
            <input
              v-model="confirmInput"
              type="text"
              :placeholder="confirmText"
              @keyup.enter="onConfirm"
            />
          </div>
        </div>
        
        <!-- Footer -->
        <div class="modal__footer">
          <button class="btn btn--secondary" @click="$emit('cancel')">
            Annuler
          </button>
          <button
            class="btn"
            :class="confirmButtonClass"
            :disabled="!canConfirm"
            @click="onConfirm"
          >
            {{ confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { DiffSummary, ApplyDiffResult } from '../types/diff';

const props = withDefaults(defineProps<{
  visible: boolean;
  title?: string;
  message?: string;
  summary?: DiffSummary;
  warnings?: string[];
  previewResult?: ApplyDiffResult;
  confirmLabel?: string;
  confirmButtonClass?: string;
  requireConfirmation?: boolean;
  confirmText?: string;
}>(), {
  title: 'Confirmation',
  message: 'Êtes-vous sûr de vouloir continuer ?',
  warnings: () => [],
  confirmLabel: 'Confirmer',
  confirmButtonClass: 'btn--primary',
  requireConfirmation: false,
  confirmText: 'CONFIRMER',
});

const emit = defineEmits<{
  (e: 'confirm'): void;
  (e: 'cancel'): void;
}>();

// État local
const confirmInput = ref('');

// Reset input quand le modal s'ouvre
watch(() => props.visible, (val) => {
  if (val) {
    confirmInput.value = '';
  }
});

// Computed
const canConfirm = computed(() => {
  if (!props.requireConfirmation) return true;
  return confirmInput.value === props.confirmText;
});

// Handlers
function onConfirm() {
  if (canConfirm.value) {
    emit('confirm');
  }
}
</script>

<style scoped>
.modal {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal__overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
}

.modal__content {
  position: relative;
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
}

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal__header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.modal__close {
  background: none;
  border: none;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.modal__close:hover {
  color: #4b5563;
}

.modal__body {
  padding: 20px;
  overflow-y: auto;
}

.modal__message {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #4b5563;
}

.modal__summary {
  margin-bottom: 16px;
}

.modal__summary h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
}

.modal__summary ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  font-size: 13px;
}

.summary-item .icon {
  font-weight: 600;
}

.summary-item--accepted {
  background: #d1fae5;
  color: #059669;
}

.summary-item--modified {
  background: #ede9fe;
  color: #7c3aed;
}

.summary-item--rejected {
  background: #fee2e2;
  color: #dc2626;
}

.summary-item--pending {
  background: #f3f4f6;
  color: #6b7280;
}

.modal__warnings {
  margin-bottom: 16px;
}

.warning {
  padding: 10px 12px;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 6px;
  color: #92400e;
  font-size: 13px;
  margin-bottom: 8px;
}

.modal__preview {
  margin-bottom: 16px;
  padding: 12px;
  background: #f3f4f6;
  border-radius: 6px;
}

.modal__preview h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  font-weight: 600;
}

.preview-stats {
  display: flex;
  gap: 16px;
}

.preview-stats .stat {
  font-size: 13px;
  color: #4b5563;
}

.modal__confirm-input {
  margin-top: 16px;
}

.modal__confirm-input label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #4b5563;
}

.modal__confirm-input strong {
  font-family: monospace;
  background: #fee2e2;
  padding: 2px 6px;
  border-radius: 4px;
  color: #dc2626;
}

.modal__confirm-input input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn--secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn--secondary:hover {
  background: #d1d5db;
}

.btn--primary {
  background: #3b82f6;
  color: white;
}

.btn--primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn--danger {
  background: #ef4444;
  color: white;
}

.btn--danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
