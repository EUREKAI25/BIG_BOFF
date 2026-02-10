<template>
  <div class="bundle-viewer">
    <div class="bundle-viewer__header" @click="expanded = !expanded">
      <span class="bundle-viewer__icon">{{ expanded ? '▼' : '▶' }}</span>
      <span class="bundle-viewer__type">{{ formatBundleType(bundle.bundle_type) }}</span>
      <span class="bundle-viewer__stats">
        <span v-if="addedCount > 0" class="stat stat--added">+{{ addedCount }}</span>
        <span v-if="removedCount > 0" class="stat stat--removed">-{{ removedCount }}</span>
        <span v-if="changedCount > 0" class="stat stat--changed">~{{ changedCount }}</span>
      </span>
    </div>
    
    <div v-show="expanded" class="bundle-viewer__content">
      <table class="bundle-viewer__table">
        <thead>
          <tr>
            <th class="col-status"></th>
            <th class="col-field">Champ</th>
            <th class="col-old">Ancienne valeur</th>
            <th class="col-new">Nouvelle valeur</th>
            <th v-if="editable" class="col-actions"></th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="change in bundle.changes" 
            :key="change.field_name"
            :class="`row--${change.change_type}`"
          >
            <td class="col-status">
              <span class="status-icon" :class="getChangeTypeClass(change.change_type)">
                {{ getChangeIcon(change.change_type) }}
              </span>
            </td>
            <td class="col-field">
              <code>{{ change.field_name }}</code>
            </td>
            <td class="col-old">
              <span 
                v-if="change.old_value !== null" 
                class="value value--old"
                :title="formatValueFull(change.old_value)"
              >
                {{ formatValue(change.old_value) }}
              </span>
              <span v-else class="value value--null">—</span>
            </td>
            <td class="col-new">
              <template v-if="isEditing(change.field_name)">
                <input
                  v-model="editValue"
                  class="edit-input"
                  @keyup.enter="saveEdit(change.field_name)"
                  @keyup.escape="cancelEdit"
                />
                <button class="btn-icon" @click="saveEdit(change.field_name)">✓</button>
                <button class="btn-icon" @click="cancelEdit">✗</button>
              </template>
              <template v-else>
                <span 
                  v-if="change.new_value !== null" 
                  class="value value--new"
                  :title="formatValueFull(change.new_value)"
                >
                  {{ formatValue(change.new_value) }}
                </span>
                <span v-else class="value value--null">—</span>
              </template>
            </td>
            <td v-if="editable" class="col-actions">
              <button 
                v-if="change.change_type !== 'unchanged' && !isEditing(change.field_name)"
                class="btn-icon btn-icon--edit"
                title="Modifier"
                @click="startEdit(change)"
              >
                ✎
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { DiffBundle, BundleFieldDiff, ChangeType } from '../types/diff';
import { getChangeTypeClass } from '../types/diff';

const props = defineProps<{
  bundle: DiffBundle;
  editable?: boolean;
}>();

const emit = defineEmits<{
  (e: 'edit', bundleType: string, fieldPath: string, newValue: unknown): void;
}>();

// État local
const expanded = ref(true);
const editingField = ref<string | null>(null);
const editValue = ref<string>('');

// Computed - compteurs
const addedCount = computed(() => 
  props.bundle.changes.filter(c => c.change_type === 'added').length
);

const removedCount = computed(() => 
  props.bundle.changes.filter(c => c.change_type === 'removed').length
);

const changedCount = computed(() => 
  props.bundle.changes.filter(c => c.change_type === 'changed').length
);

// Formatters
function formatBundleType(type: string): string {
  const labels: Record<string, string> = {
    attributes: 'Attributs',
    methods: 'Méthodes',
    rules: 'Règles',
    relations: 'Relations',
    tags: 'Tags',
  };
  return labels[type] || type;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'string') {
    return value.length > 50 ? value.slice(0, 47) + '...' : value;
  }
  if (typeof value === 'object') {
    const str = JSON.stringify(value);
    return str.length > 50 ? str.slice(0, 47) + '...' : str;
  }
  return String(value);
}

function formatValueFull(value: unknown): string {
  if (value === null || value === undefined) return '';
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}

function getChangeIcon(type: ChangeType): string {
  const icons: Record<ChangeType, string> = {
    added: '+',
    removed: '−',
    changed: '~',
    unchanged: '=',
  };
  return icons[type];
}

// Édition
function isEditing(fieldName: string): boolean {
  return editingField.value === fieldName;
}

function startEdit(change: BundleFieldDiff): void {
  editingField.value = change.field_name;
  editValue.value = formatValueFull(change.new_value);
}

function cancelEdit(): void {
  editingField.value = null;
  editValue.value = '';
}

function saveEdit(fieldName: string): void {
  try {
    // Tenter de parser comme JSON si possible
    let parsedValue: unknown;
    try {
      parsedValue = JSON.parse(editValue.value);
    } catch {
      parsedValue = editValue.value;
    }
    
    emit('edit', props.bundle.bundle_type, fieldName, parsedValue);
  } finally {
    cancelEdit();
  }
}
</script>

<style scoped>
.bundle-viewer {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}

.bundle-viewer__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f9fafb;
  cursor: pointer;
  user-select: none;
}

.bundle-viewer__header:hover {
  background: #f3f4f6;
}

.bundle-viewer__icon {
  font-size: 10px;
  color: #6b7280;
}

.bundle-viewer__type {
  font-weight: 600;
  font-size: 14px;
}

.bundle-viewer__stats {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.stat {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
}

.stat--added {
  background: #d1fae5;
  color: #059669;
}

.stat--removed {
  background: #fee2e2;
  color: #dc2626;
}

.stat--changed {
  background: #fef3c7;
  color: #d97706;
}

.bundle-viewer__content {
  border-top: 1px solid #e5e7eb;
}

.bundle-viewer__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.bundle-viewer__table th,
.bundle-viewer__table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid #f3f4f6;
}

.bundle-viewer__table th {
  font-weight: 500;
  font-size: 11px;
  text-transform: uppercase;
  color: #6b7280;
  background: #fafafa;
}

.col-status {
  width: 30px;
  text-align: center;
}

.col-field {
  width: 25%;
}

.col-old,
.col-new {
  width: 30%;
}

.col-actions {
  width: 40px;
  text-align: center;
}

.status-icon {
  display: inline-block;
  width: 20px;
  height: 20px;
  line-height: 20px;
  text-align: center;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

code {
  font-family: monospace;
  font-size: 12px;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
}

.value {
  display: inline-block;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: monospace;
  font-size: 12px;
}

.value--old {
  color: #dc2626;
}

.value--new {
  color: #059669;
}

.value--null {
  color: #9ca3af;
}

.row--added {
  background: #f0fdf4;
}

.row--removed {
  background: #fef2f2;
}

.row--changed {
  background: #fffbeb;
}

.row--unchanged {
  opacity: 0.6;
}

.edit-input {
  width: 150px;
  padding: 4px 8px;
  border: 1px solid #3b82f6;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
}

.btn-icon {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.6;
}

.btn-icon:hover {
  opacity: 1;
}

.btn-icon--edit {
  color: #3b82f6;
}
</style>
