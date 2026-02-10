<template>
  <div class="decision-controls">
    <!-- État actuel -->
    <div class="decision-controls__status">
      <span class="decision-controls__label">Décision:</span>
      <span class="decision-controls__value" :class="decisionClass">
        {{ formatDecision(decision) }}
      </span>
    </div>
    
    <!-- Boutons d'action -->
    <div class="decision-controls__actions">
      <!-- Accepter -->
      <button
        class="btn btn--success"
        :class="{ 'btn--active': decision === 'accepted' }"
        :disabled="decision === 'accepted'"
        @click="$emit('accept')"
      >
        <span class="btn__icon">✓</span>
        Accepter
      </button>
      
      <!-- Refuser -->
      <button
        class="btn btn--danger"
        :class="{ 'btn--active': decision === 'rejected' }"
        :disabled="decision === 'rejected'"
        @click="$emit('reject')"
      >
        <span class="btn__icon">✗</span>
        Refuser
      </button>
      
      <!-- Modifier -->
      <button
        v-if="showModifyButton"
        class="btn btn--purple"
        :class="{ 'btn--active': decision === 'modified' }"
        @click="openModifyDialog"
      >
        <span class="btn__icon">✎</span>
        Modifier
      </button>
      
      <!-- Réinitialiser -->
      <button
        class="btn btn--secondary"
        :disabled="decision === 'pending'"
        @click="$emit('reset')"
      >
        <span class="btn__icon">↺</span>
        Reset
      </button>
    </div>
    
    <!-- Zone de commentaire -->
    <div v-if="showComment" class="decision-controls__comment">
      <label>Commentaire (optionnel):</label>
      <textarea
        v-model="localComment"
        placeholder="Justification de la décision..."
        rows="2"
      ></textarea>
    </div>
    
    <!-- Dialog de modification -->
    <div v-if="showModifyDialog" class="modify-dialog">
      <div class="modify-dialog__overlay" @click="closeModifyDialog"></div>
      <div class="modify-dialog__content">
        <h4>Accepter avec modifications</h4>
        <p>Vous pouvez modifier les valeurs proposées avant d'accepter.</p>
        
        <div class="modify-dialog__comment">
          <label>Commentaire:</label>
          <textarea
            v-model="modifyComment"
            placeholder="Raison de la modification..."
            rows="3"
          ></textarea>
        </div>
        
        <div class="modify-dialog__actions">
          <button class="btn btn--secondary" @click="closeModifyDialog">
            Annuler
          </button>
          <button class="btn btn--purple" @click="confirmModify">
            Confirmer la modification
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { Decision } from '../types/diff';
import { formatDecision, getDecisionClass } from '../types/diff';

const props = defineProps<{
  decision: Decision;
  hasOverrides?: boolean;
  comment?: string;
}>();

const emit = defineEmits<{
  (e: 'accept'): void;
  (e: 'reject'): void;
  (e: 'modify', comment?: string): void;
  (e: 'reset'): void;
}>();

// État local
const localComment = ref(props.comment || '');
const showModifyDialog = ref(false);
const modifyComment = ref('');

// Sync commentaire avec prop
watch(() => props.comment, (val) => {
  localComment.value = val || '';
});

// Computed
const decisionClass = computed(() => getDecisionClass(props.decision));

const showComment = computed(() => 
  props.decision !== 'pending'
);

const showModifyButton = computed(() => 
  props.decision === 'pending' || props.decision === 'modified'
);

// Handlers
function openModifyDialog(): void {
  modifyComment.value = props.comment || '';
  showModifyDialog.value = true;
}

function closeModifyDialog(): void {
  showModifyDialog.value = false;
  modifyComment.value = '';
}

function confirmModify(): void {
  emit('modify', modifyComment.value || undefined);
  closeModifyDialog();
}
</script>

<style scoped>
.decision-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.decision-controls__status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.decision-controls__label {
  font-size: 13px;
  color: #6b7280;
}

.decision-controls__value {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
}

.decision-controls__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn__icon {
  font-size: 14px;
}

.btn--success {
  background: #10b981;
  color: white;
}

.btn--success:hover:not(:disabled) {
  background: #059669;
}

.btn--danger {
  background: #ef4444;
  color: white;
}

.btn--danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn--purple {
  background: #8b5cf6;
  color: white;
}

.btn--purple:hover:not(:disabled) {
  background: #7c3aed;
}

.btn--secondary {
  background: #6b7280;
  color: white;
}

.btn--secondary:hover:not(:disabled) {
  background: #4b5563;
}

.btn--active {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.decision-controls__comment {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.decision-controls__comment label {
  font-size: 12px;
  color: #6b7280;
}

.decision-controls__comment textarea {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  resize: vertical;
  min-height: 60px;
}

/* Dialog de modification */
.modify-dialog {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modify-dialog__overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
}

.modify-dialog__content {
  position: relative;
  background: white;
  padding: 24px;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modify-dialog__content h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
}

.modify-dialog__content p {
  margin: 0 0 16px 0;
  color: #6b7280;
  font-size: 14px;
}

.modify-dialog__comment {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.modify-dialog__comment label {
  font-size: 13px;
  font-weight: 500;
}

.modify-dialog__comment textarea {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
}

.modify-dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
