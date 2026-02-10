<template>
  <div
    class="diff-list-item"
    :class="{
      'diff-list-item--selected': selected,
      [`diff-list-item--${object.operation}`]: true,
      [`diff-list-item--decision-${object.decision}`]: true,
    }"
    @click="$emit('click')"
  >
    <!-- Indicateur d'opération -->
    <div class="diff-list-item__operation" :class="operationClass">
      {{ operationIcon }}
    </div>
    
    <!-- Contenu principal -->
    <div class="diff-list-item__content">
      <div class="diff-list-item__header">
        <span class="diff-list-item__type">{{ object.object_type }}</span>
        <span class="diff-list-item__id">{{ shortId }}</span>
      </div>
      
      <div class="diff-list-item__path" :title="object.object_path">
        {{ object.object_label || truncatedPath }}
      </div>
      
      <div class="diff-list-item__meta">
        <span class="diff-list-item__changes">
          {{ changeCount }} changement{{ changeCount > 1 ? 's' : '' }}
        </span>
        <span 
          v-if="bundleTypes.length > 0" 
          class="diff-list-item__bundles"
        >
          {{ bundleTypes.join(', ') }}
        </span>
      </div>
    </div>
    
    <!-- Indicateur de décision -->
    <div class="diff-list-item__decision" :class="decisionClass">
      <span class="diff-list-item__decision-icon">{{ decisionIcon }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { DiffObject } from '../types/diff';
import { getActiveBundles, countChanges, getOperationClass, getDecisionClass } from '../types/diff';

const props = defineProps<{
  object: DiffObject;
  selected: boolean;
}>();

defineEmits<{
  (e: 'click'): void;
}>();

// Computed
const shortId = computed(() => {
  const id = props.object.object_id;
  return id.length > 12 ? `${id.slice(0, 8)}...` : id;
});

const truncatedPath = computed(() => {
  const path = props.object.object_path;
  if (path.length <= 40) return path;
  return '...' + path.slice(-37);
});

const changeCount = computed(() => countChanges(props.object));

const bundleTypes = computed(() => {
  return getActiveBundles(props.object).map(b => {
    const labels: Record<string, string> = {
      attributes: 'attr',
      methods: 'meth',
      rules: 'rules',
      relations: 'rel',
      tags: 'tags',
    };
    return labels[b.bundle_type] || b.bundle_type;
  });
});

const operationIcon = computed(() => {
  const icons: Record<string, string> = {
    create: '+',
    update: '~',
    delete: '−',
    disable: '○',
  };
  return icons[props.object.operation] || '?';
});

const operationClass = computed(() => getOperationClass(props.object.operation));

const decisionIcon = computed(() => {
  const icons: Record<string, string> = {
    pending: '?',
    accepted: '✓',
    rejected: '✗',
    modified: '✎',
  };
  return icons[props.object.decision] || '?';
});

const decisionClass = computed(() => getDecisionClass(props.object.decision));
</script>

<style scoped>
.diff-list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 4px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
}

.diff-list-item:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.diff-list-item--selected {
  background: #eff6ff;
  border-color: #3b82f6;
}

.diff-list-item__operation {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-weight: 600;
  font-size: 16px;
}

.diff-list-item__content {
  flex: 1;
  min-width: 0;
}

.diff-list-item__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.diff-list-item__type {
  font-weight: 600;
  font-size: 13px;
  color: #374151;
}

.diff-list-item__id {
  font-family: monospace;
  font-size: 11px;
  color: #9ca3af;
}

.diff-list-item__path {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.diff-list-item__meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #9ca3af;
}

.diff-list-item__bundles {
  font-family: monospace;
}

.diff-list-item__decision {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 12px;
}

/* Décisions colorées */
.diff-list-item--decision-pending .diff-list-item__decision {
  background: #f3f4f6;
  color: #6b7280;
}

.diff-list-item--decision-accepted .diff-list-item__decision {
  background: #d1fae5;
  color: #059669;
}

.diff-list-item--decision-rejected .diff-list-item__decision {
  background: #fee2e2;
  color: #dc2626;
}

.diff-list-item--decision-modified .diff-list-item__decision {
  background: #ede9fe;
  color: #7c3aed;
}
</style>
