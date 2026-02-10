<template>
  <div class="diff-detail" v-if="object">
    <!-- Header -->
    <div class="diff-detail__header">
      <div class="diff-detail__title">
        <span class="diff-detail__operation" :class="operationClass">
          {{ formatOperation(object.operation) }}
        </span>
        <h3>{{ object.object_type }}</h3>
      </div>
      
      <div class="diff-detail__meta">
        <div class="diff-detail__meta-item">
          <span class="label">ID:</span>
          <code>{{ object.object_id }}</code>
        </div>
        <div class="diff-detail__meta-item">
          <span class="label">Chemin:</span>
          <code>{{ object.object_path }}</code>
        </div>
        <div v-if="object.object_label" class="diff-detail__meta-item">
          <span class="label">Label:</span>
          <span>{{ object.object_label }}</span>
        </div>
      </div>
    </div>
    
    <!-- Bundles -->
    <div class="diff-detail__bundles">
      <BundleDiffViewer
        v-for="bundle in activeBundles"
        :key="bundle.bundle_type"
        :bundle="bundle"
        :editable="object.decision === 'pending' || object.decision === 'modified'"
        @edit="onBundleEdit"
      />
      
      <div v-if="activeBundles.length === 0" class="diff-detail__no-changes">
        <p>Aucun changement détaillé pour cette opération.</p>
      </div>
    </div>
    
    <!-- Contrôles de décision -->
    <div class="diff-detail__controls">
      <DecisionControls
        :decision="object.decision"
        :has-overrides="object.user_overrides.length > 0"
        :comment="object.user_comment"
        @accept="$emit('accept', object.diff_object_id)"
        @reject="$emit('reject', object.diff_object_id)"
        @modify="onModify"
        @reset="$emit('reset', object.diff_object_id)"
      />
    </div>
    
    <!-- Informations de décision -->
    <div v-if="object.decided_at" class="diff-detail__decision-info">
      <p>
        <strong>{{ formatDecision(object.decision) }}</strong>
        par {{ object.decided_by }}
        le {{ formatDate(object.decided_at) }}
      </p>
      <p v-if="object.user_comment" class="diff-detail__comment">
        « {{ object.user_comment }} »
      </p>
      
      <!-- Overrides -->
      <div v-if="object.user_overrides.length > 0" class="diff-detail__overrides">
        <h4>Modifications utilisateur:</h4>
        <ul>
          <li v-for="(override, idx) in object.user_overrides" :key="idx">
            <code>{{ override.field_path }}</code>:
            <span class="old-value">{{ formatValue(override.original_proposed) }}</span>
            →
            <span class="new-value">{{ formatValue(override.user_value) }}</span>
            <span v-if="override.reason" class="reason">({{ override.reason }})</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
  
  <!-- État vide -->
  <div v-else class="diff-detail diff-detail--empty">
    <p>Sélectionnez un changement pour voir ses détails.</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { DiffObject, DiffBundle, UserOverride } from '../types/diff';
import { 
  getActiveBundles, 
  formatOperation, 
  formatDecision, 
  getOperationClass 
} from '../types/diff';
import BundleDiffViewer from './BundleDiffViewer.vue';
import DecisionControls from './DecisionControls.vue';

const props = defineProps<{
  object: DiffObject | null;
}>();

const emit = defineEmits<{
  (e: 'accept', id: string): void;
  (e: 'reject', id: string): void;
  (e: 'modify', id: string, overrides: UserOverride[], comment?: string): void;
  (e: 'reset', id: string): void;
}>();

// Computed
const activeBundles = computed(() => {
  if (!props.object) return [];
  return getActiveBundles(props.object);
});

const operationClass = computed(() => {
  if (!props.object) return '';
  return getOperationClass(props.object.operation);
});

// Handlers
function onBundleEdit(bundleType: string, fieldPath: string, newValue: unknown) {
  if (!props.object) return;
  
  // Trouver la valeur originale
  const bundle = activeBundles.value.find(b => b.bundle_type === bundleType);
  const change = bundle?.changes.find(c => c.field_name === fieldPath);
  
  if (change) {
    const override: UserOverride = {
      field_path: `${bundleType}.${fieldPath}`,
      original_proposed: change.new_value,
      user_value: newValue,
    };
    
    emit('modify', props.object.diff_object_id, [override]);
  }
}

function onModify(comment?: string) {
  if (!props.object) return;
  emit('modify', props.object.diff_object_id, props.object.user_overrides, comment);
}

// Formatters
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatValue(value: unknown): string {
  if (value === null) return 'null';
  if (value === undefined) return 'undefined';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
</script>

<style scoped>
.diff-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.diff-detail--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}

.diff-detail__header {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.diff-detail__title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.diff-detail__title h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.diff-detail__operation {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid;
}

.diff-detail__meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.diff-detail__meta-item {
  font-size: 13px;
  color: #6b7280;
}

.diff-detail__meta-item .label {
  font-weight: 500;
  margin-right: 8px;
}

.diff-detail__meta-item code {
  font-family: monospace;
  font-size: 12px;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
}

.diff-detail__bundles {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.diff-detail__no-changes {
  text-align: center;
  padding: 32px;
  color: #9ca3af;
}

.diff-detail__controls {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.diff-detail__decision-info {
  padding: 12px 16px;
  background: #f3f4f6;
  border-top: 1px solid #e5e7eb;
  font-size: 13px;
}

.diff-detail__decision-info p {
  margin: 0 0 8px 0;
}

.diff-detail__comment {
  font-style: italic;
  color: #6b7280;
}

.diff-detail__overrides {
  margin-top: 12px;
}

.diff-detail__overrides h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  font-weight: 600;
}

.diff-detail__overrides ul {
  margin: 0;
  padding-left: 20px;
}

.diff-detail__overrides li {
  margin-bottom: 4px;
  font-size: 12px;
}

.diff-detail__overrides code {
  font-family: monospace;
  background: #e5e7eb;
  padding: 1px 4px;
  border-radius: 3px;
}

.diff-detail__overrides .old-value {
  color: #dc2626;
  text-decoration: line-through;
}

.diff-detail__overrides .new-value {
  color: #059669;
  font-weight: 500;
}

.diff-detail__overrides .reason {
  color: #9ca3af;
  font-style: italic;
}
</style>
