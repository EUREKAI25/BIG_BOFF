/**
 * H3 — Types TypeScript pour le Diff & Validation
 * ================================================
 * 
 * Types miroirs des modèles Python Pydantic.
 * Utilisés par le store Pinia et les composants Vue.
 */

// =============================================================================
// ENUMS
// =============================================================================

export type Operation = 'create' | 'update' | 'delete' | 'disable';

export type DiffStatus = 
  | 'pending' 
  | 'partial' 
  | 'validated' 
  | 'applied' 
  | 'rejected' 
  | 'cancelled' 
  | 'error';

export type Decision = 'pending' | 'accepted' | 'rejected' | 'modified';

export type ChangeType = 'added' | 'removed' | 'changed' | 'unchanged';

export type BundleType = 'attributes' | 'methods' | 'rules' | 'relations' | 'tags';


// =============================================================================
// MODÈLES DE BASE
// =============================================================================

export interface BundleFieldDiff {
  field_name: string;
  old_value: unknown;
  new_value: unknown;
  change_type: ChangeType;
}

export interface DiffBundle {
  bundle_type: BundleType;
  changes: BundleFieldDiff[];
}

export interface UserOverride {
  field_path: string;
  original_proposed: unknown;
  user_value: unknown;
  reason?: string;
}


// =============================================================================
// DIFF OBJECT
// =============================================================================

export interface DiffObject {
  diff_object_id: string;
  object_id: string;
  object_type: string;
  object_path: string;
  object_label?: string;
  
  operation: Operation;
  
  attributes?: DiffBundle;
  methods?: DiffBundle;
  rules?: DiffBundle;
  relations?: DiffBundle;
  tags?: DiffBundle;
  
  decision: Decision;
  user_overrides: UserOverride[];
  user_comment?: string;
  decided_at?: string;
  decided_by?: string;
}


// =============================================================================
// DIFF GLOBAL
// =============================================================================

export interface DiffSummary {
  total_objects: number;
  created_count: number;
  updated_count: number;
  deleted_count: number;
  disabled_count: number;
  pending_count: number;
  accepted_count: number;
  rejected_count: number;
  modified_count: number;
}

export interface DiffGlobal {
  diff_id: string;
  scenario_id: string;
  scenario_name?: string;
  scenario_description?: string;
  
  created_at: string;
  updated_at: string;
  applied_at?: string;
  
  status: DiffStatus;
  objects: DiffObject[];
  summary: DiffSummary;
  
  applied_by?: string;
  application_error?: string;
}


// =============================================================================
// REQUÊTES API
// =============================================================================

export interface DecisionRequest {
  diff_object_id: string;
  decision: Decision;
  overrides?: UserOverride[];
  comment?: string;
}

export interface BulkDecisionRequest {
  diff_id: string;
  decisions: DecisionRequest[];
  user_id: string;
}

export interface ApplyDiffRequest {
  diff_id: string;
  user_id: string;
  dry_run?: boolean;
}

export interface ApplyDiffResult {
  diff_id: string;
  success: boolean;
  applied_count: number;
  skipped_count: number;
  error_count: number;
  errors: Array<{
    diff_object_id: string;
    object_id: string;
    error: string;
  }>;
}


// =============================================================================
// FILTRES ET OPTIONS UI
// =============================================================================

export interface DiffFilters {
  operation?: Operation[];
  decision?: Decision[];
  bundle_type?: BundleType[];
  search?: string;
}

export interface GroupedDiffObjects {
  byOperation: Record<Operation, DiffObject[]>;
  byType: Record<string, DiffObject[]>;
  byDecision: Record<Decision, DiffObject[]>;
}

export type GroupBy = 'operation' | 'type' | 'decision' | 'none';


// =============================================================================
// HELPERS
// =============================================================================

/**
 * Vérifie si un DiffObject a des changements actifs.
 */
export function hasActiveChanges(obj: DiffObject): boolean {
  const bundles = [obj.attributes, obj.methods, obj.rules, obj.relations, obj.tags];
  return bundles.some(b => 
    b && b.changes.some(c => c.change_type !== 'unchanged')
  );
}

/**
 * Compte le total des changements d'un DiffObject.
 */
export function countChanges(obj: DiffObject): number {
  const bundles = [obj.attributes, obj.methods, obj.rules, obj.relations, obj.tags];
  return bundles.reduce((sum, b) => sum + (b?.changes.length ?? 0), 0);
}

/**
 * Retourne les bundles avec des changements.
 */
export function getActiveBundles(obj: DiffObject): DiffBundle[] {
  const bundles = [obj.attributes, obj.methods, obj.rules, obj.relations, obj.tags];
  return bundles.filter((b): b is DiffBundle => 
    b !== undefined && b.changes.some(c => c.change_type !== 'unchanged')
  );
}

/**
 * Formate un label d'opération.
 */
export function formatOperation(op: Operation): string {
  const labels: Record<Operation, string> = {
    create: 'Création',
    update: 'Modification',
    delete: 'Suppression',
    disable: 'Désactivation',
  };
  return labels[op];
}

/**
 * Formate un label de décision.
 */
export function formatDecision(dec: Decision): string {
  const labels: Record<Decision, string> = {
    pending: 'En attente',
    accepted: 'Accepté',
    rejected: 'Refusé',
    modified: 'Modifié',
  };
  return labels[dec];
}

/**
 * Formate un label de statut.
 */
export function formatStatus(status: DiffStatus): string {
  const labels: Record<DiffStatus, string> = {
    pending: 'En attente',
    partial: 'Partiellement validé',
    validated: 'Validé',
    applied: 'Appliqué',
    rejected: 'Rejeté',
    cancelled: 'Annulé',
    error: 'Erreur',
  };
  return labels[status];
}

/**
 * Retourne une classe CSS pour un type de changement.
 */
export function getChangeTypeClass(type: ChangeType): string {
  const classes: Record<ChangeType, string> = {
    added: 'text-green-600 bg-green-50',
    removed: 'text-red-600 bg-red-50',
    changed: 'text-amber-600 bg-amber-50',
    unchanged: 'text-gray-400 bg-gray-50',
  };
  return classes[type];
}

/**
 * Retourne une classe CSS pour une opération.
 */
export function getOperationClass(op: Operation): string {
  const classes: Record<Operation, string> = {
    create: 'text-green-700 bg-green-100 border-green-200',
    update: 'text-blue-700 bg-blue-100 border-blue-200',
    delete: 'text-red-700 bg-red-100 border-red-200',
    disable: 'text-orange-700 bg-orange-100 border-orange-200',
  };
  return classes[op];
}

/**
 * Retourne une classe CSS pour une décision.
 */
export function getDecisionClass(dec: Decision): string {
  const classes: Record<Decision, string> = {
    pending: 'text-gray-600 bg-gray-100',
    accepted: 'text-green-600 bg-green-100',
    rejected: 'text-red-600 bg-red-100',
    modified: 'text-purple-600 bg-purple-100',
  };
  return classes[dec];
}
