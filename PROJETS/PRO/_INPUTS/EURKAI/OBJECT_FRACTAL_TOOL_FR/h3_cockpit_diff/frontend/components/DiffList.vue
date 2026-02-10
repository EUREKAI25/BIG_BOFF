<template>
  <div class="diff-list">
    <!-- Header avec filtres -->
    <div class="diff-list__header">
      <div class="diff-list__title">
        <h3>Changements proposés</h3>
        <span class="diff-list__count">
          {{ filteredObjects.length }} / {{ totalCount }}
        </span>
      </div>
      
      <!-- Barre de recherche -->
      <div class="diff-list__search">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Rechercher..."
          class="diff-list__search-input"
          @input="onSearchChange"
        />
      </div>
      
      <!-- Filtres -->
      <div class="diff-list__filters">
        <!-- Filtre par opération -->
        <select 
          v-model="operationFilter" 
          class="diff-list__filter-select"
          @change="onFilterChange"
        >
          <option value="">Toutes opérations</option>
          <option value="create">Créations</option>
          <option value="update">Modifications</option>
          <option value="delete">Suppressions</option>
          <option value="disable">Désactivations</option>
        </select>
        
        <!-- Filtre par décision -->
        <select 
          v-model="decisionFilter" 
          class="diff-list__filter-select"
          @change="onFilterChange"
        >
          <option value="">Toutes décisions</option>
          <option value="pending">En attente</option>
          <option value="accepted">Acceptés</option>
          <option value="rejected">Refusés</option>
          <option value="modified">Modifiés</option>
        </select>
        
        <!-- Groupement -->
        <select 
          v-model="groupByMode" 
          class="diff-list__filter-select"
          @change="onGroupByChange"
        >
          <option value="none">Sans groupement</option>
          <option value="operation">Par opération</option>
          <option value="type">Par type d'objet</option>
          <option value="decision">Par décision</option>
        </select>
      </div>
    </div>
    
    <!-- Actions groupées -->
    <div class="diff-list__bulk-actions">
      <button 
        class="btn btn--success btn--sm"
        :disabled="pendingCount === 0"
        @click="$emit('accept-all')"
      >
        ✓ Tout accepter ({{ pendingCount }})
      </button>
      <button 
        class="btn btn--danger btn--sm"
        :disabled="pendingCount === 0"
        @click="$emit('reject-all')"
      >
        ✗ Tout refuser ({{ pendingCount }})
      </button>
      <button 
        class="btn btn--secondary btn--sm"
        :disabled="decidedCount === 0"
        @click="$emit('reset-all')"
      >
        ↺ Réinitialiser
      </button>
    </div>
    
    <!-- Liste des objets -->
    <div class="diff-list__content">
      <!-- Mode sans groupement -->
      <template v-if="groupByMode === 'none'">
        <DiffListItem
          v-for="obj in filteredObjects"
          :key="obj.diff_object_id"
          :object="obj"
          :selected="obj.diff_object_id === selectedId"
          @click="$emit('select', obj.diff_object_id)"
        />
      </template>
      
      <!-- Mode groupé -->
      <template v-else>
        <div
          v-for="(objects, groupKey) in groupedObjects"
          :key="groupKey"
          class="diff-list__group"
        >
          <div class="diff-list__group-header">
            <span class="diff-list__group-label">
              {{ formatGroupLabel(groupKey) }}
            </span>
            <span class="diff-list__group-count">
              {{ objects.length }}
            </span>
          </div>
          
          <DiffListItem
            v-for="obj in objects"
            :key="obj.diff_object_id"
            :object="obj"
            :selected="obj.diff_object_id === selectedId"
            @click="$emit('select', obj.diff_object_id)"
          />
        </div>
      </template>
      
      <!-- État vide -->
      <div v-if="filteredObjects.length === 0" class="diff-list__empty">
        <p>Aucun changement ne correspond aux filtres.</p>
        <button class="btn btn--link" @click="clearFilters">
          Effacer les filtres
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { DiffObject, Operation, Decision, GroupBy } from '../types/diff';
import { formatOperation, formatDecision } from '../types/diff';
import DiffListItem from './DiffListItem.vue';

// Props
const props = defineProps<{
  objects: DiffObject[];
  selectedId: string | null;
  groupBy: GroupBy;
}>();

// Emits
const emit = defineEmits<{
  (e: 'select', id: string): void;
  (e: 'accept-all'): void;
  (e: 'reject-all'): void;
  (e: 'reset-all'): void;
  (e: 'filter-change', filters: { operation?: Operation; decision?: Decision; search?: string }): void;
  (e: 'group-by-change', mode: GroupBy): void;
}>();

// État local des filtres
const searchQuery = ref('');
const operationFilter = ref<Operation | ''>('');
const decisionFilter = ref<Decision | ''>('');
const groupByMode = ref<GroupBy>(props.groupBy);

// Sync groupBy avec prop
watch(() => props.groupBy, (val) => {
  groupByMode.value = val;
});

// Objets filtrés
const filteredObjects = computed(() => {
  let result = props.objects;
  
  if (operationFilter.value) {
    result = result.filter(o => o.operation === operationFilter.value);
  }
  
  if (decisionFilter.value) {
    result = result.filter(o => o.decision === decisionFilter.value);
  }
  
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    result = result.filter(o =>
      o.object_id.toLowerCase().includes(q) ||
      o.object_path.toLowerCase().includes(q) ||
      o.object_type.toLowerCase().includes(q) ||
      (o.object_label?.toLowerCase().includes(q) ?? false)
    );
  }
  
  return result;
});

// Objets groupés
const groupedObjects = computed(() => {
  if (groupByMode.value === 'none') return {};
  
  const groups: Record<string, DiffObject[]> = {};
  
  for (const obj of filteredObjects.value) {
    let key: string;
    switch (groupByMode.value) {
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

// Compteurs
const totalCount = computed(() => props.objects.length);

const pendingCount = computed(() => 
  props.objects.filter(o => o.decision === 'pending').length
);

const decidedCount = computed(() => 
  props.objects.filter(o => o.decision !== 'pending').length
);

// Handlers
function onSearchChange() {
  emitFilters();
}

function onFilterChange() {
  emitFilters();
}

function onGroupByChange() {
  emit('group-by-change', groupByMode.value);
}

function emitFilters() {
  emit('filter-change', {
    operation: operationFilter.value || undefined,
    decision: decisionFilter.value || undefined,
    search: searchQuery.value || undefined,
  });
}

function clearFilters() {
  searchQuery.value = '';
  operationFilter.value = '';
  decisionFilter.value = '';
  emitFilters();
}

function formatGroupLabel(key: string): string {
  if (groupByMode.value === 'operation') {
    return formatOperation(key as Operation);
  }
  if (groupByMode.value === 'decision') {
    return formatDecision(key as Decision);
  }
  return key;
}
</script>

<style scoped>
.diff-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}

.diff-list__header {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.diff-list__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.diff-list__title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.diff-list__count {
  font-size: 13px;
  color: #6b7280;
}

.diff-list__search {
  margin-bottom: 12px;
}

.diff-list__search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.diff-list__filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.diff-list__filter-select {
  flex: 1;
  min-width: 120px;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
}

.diff-list__bulk-actions {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.diff-list__content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.diff-list__group {
  margin-bottom: 16px;
}

.diff-list__group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  margin-bottom: 4px;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
}

.diff-list__group-count {
  background: #e5e7eb;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.diff-list__empty {
  text-align: center;
  padding: 32px;
  color: #6b7280;
}

/* Boutons */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn--sm {
  padding: 6px 12px;
  font-size: 12px;
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

.btn--secondary {
  background: #6b7280;
  color: white;
}

.btn--secondary:hover:not(:disabled) {
  background: #4b5563;
}

.btn--link {
  background: none;
  color: #3b82f6;
  padding: 4px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
