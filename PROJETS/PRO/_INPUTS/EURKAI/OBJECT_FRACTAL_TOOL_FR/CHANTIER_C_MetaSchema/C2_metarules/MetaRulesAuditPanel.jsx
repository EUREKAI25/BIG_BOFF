/**
 * EUREKAI C2/2 — MetaRules Audit Panel
 * ====================================
 * Composant React pour l'intégration cockpit du système d'audit MetaRules.
 * 
 * Features:
 * - Affichage du résultat d'audit global
 * - Liste filtrables des violations par sévérité
 * - Détail de chaque violation avec suggestions
 * - Contrôle des règles (enable/disable)
 * - Export du rapport
 */

import React, { useState, useMemo, useCallback } from 'react';

// =============================================================================
// TYPES
// =============================================================================

/**
 * @typedef {'critical' | 'error' | 'warning' | 'info'} Severity
 * @typedef {'identity' | 'structure' | 'bundle' | 'relation' | 'consistency'} RuleCategory
 */

/**
 * @typedef {Object} Violation
 * @property {string} ruleId
 * @property {string} ruleName
 * @property {string} objectId
 * @property {string} objectLineage
 * @property {Severity} severity
 * @property {string} message
 * @property {string} [suggestion]
 * @property {Object} [context]
 */

/**
 * @typedef {Object} AuditResult
 * @property {boolean} ok
 * @property {Violation[]} errors
 * @property {Object} stats
 * @property {string} timestamp
 */

/**
 * @typedef {Object} RuleInfo
 * @property {string} id
 * @property {string} name
 * @property {string} description
 * @property {RuleCategory} category
 * @property {Severity} severity
 * @property {boolean} enabled
 * @property {string} erk
 */

// =============================================================================
// CONSTANTES ET HELPERS
// =============================================================================

const SEVERITY_CONFIG = {
  critical: {
    icon: '🔴',
    color: '#dc2626',
    bgColor: '#fef2f2',
    label: 'Critique',
    order: 0
  },
  error: {
    icon: '🟠',
    color: '#ea580c',
    bgColor: '#fff7ed',
    label: 'Erreur',
    order: 1
  },
  warning: {
    icon: '🟡',
    color: '#ca8a04',
    bgColor: '#fefce8',
    label: 'Avertissement',
    order: 2
  },
  info: {
    icon: '🔵',
    color: '#2563eb',
    bgColor: '#eff6ff',
    label: 'Information',
    order: 3
  }
};

const CATEGORY_LABELS = {
  identity: 'Identité',
  structure: 'Structure',
  bundle: 'Bundle',
  relation: 'Relations',
  consistency: 'Cohérence'
};

// =============================================================================
// COMPOSANTS
// =============================================================================

/**
 * Badge de sévérité
 */
const SeverityBadge = ({ severity }) => {
  const config = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.info;
  
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '2px 8px',
        borderRadius: '9999px',
        fontSize: '12px',
        fontWeight: 500,
        backgroundColor: config.bgColor,
        color: config.color,
        border: `1px solid ${config.color}20`
      }}
    >
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </span>
  );
};

/**
 * Carte de statistiques
 */
const StatCard = ({ label, value, icon, color }) => (
  <div
    style={{
      padding: '16px',
      backgroundColor: '#fff',
      borderRadius: '8px',
      border: '1px solid #e5e7eb',
      textAlign: 'center',
      minWidth: '100px'
    }}
  >
    <div style={{ fontSize: '24px', marginBottom: '4px' }}>{icon}</div>
    <div style={{ fontSize: '24px', fontWeight: 700, color }}>{value}</div>
    <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>{label}</div>
  </div>
);

/**
 * Carte de violation individuelle
 */
const ViolationCard = ({ violation, onObjectClick }) => {
  const [expanded, setExpanded] = useState(false);
  const config = SEVERITY_CONFIG[violation.severity];
  
  return (
    <div
      style={{
        padding: '12px 16px',
        backgroundColor: '#fff',
        borderRadius: '8px',
        border: `1px solid ${config.color}30`,
        borderLeft: `4px solid ${config.color}`,
        marginBottom: '8px'
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <SeverityBadge severity={violation.severity} />
            <span style={{ fontSize: '12px', color: '#6b7280', fontFamily: 'monospace' }}>
              [{violation.ruleId}]
            </span>
          </div>
          
          <div
            style={{
              fontFamily: 'monospace',
              fontSize: '13px',
              color: '#374151',
              cursor: 'pointer',
              textDecoration: 'underline',
              textDecorationColor: '#d1d5db'
            }}
            onClick={() => onObjectClick?.(violation.objectId)}
            title="Cliquer pour voir l'objet"
          >
            {violation.objectLineage || violation.objectId}
          </div>
        </div>
        
        <button
          onClick={() => setExpanded(!expanded)}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '18px',
            color: '#6b7280',
            padding: '4px'
          }}
          title={expanded ? 'Réduire' : 'Développer'}
        >
          {expanded ? '▲' : '▼'}
        </button>
      </div>
      
      {/* Message */}
      <p style={{ margin: '8px 0 0', fontSize: '14px', color: '#374151' }}>
        {violation.message}
      </p>
      
      {/* Details (expanded) */}
      {expanded && (
        <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #e5e7eb' }}>
          {violation.suggestion && (
            <div style={{ marginBottom: '8px' }}>
              <strong style={{ fontSize: '12px', color: '#6b7280' }}>💡 Suggestion:</strong>
              <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#059669' }}>
                {violation.suggestion}
              </p>
            </div>
          )}
          
          {violation.context && Object.keys(violation.context).length > 0 && (
            <div>
              <strong style={{ fontSize: '12px', color: '#6b7280' }}>📋 Contexte:</strong>
              <pre
                style={{
                  margin: '4px 0 0',
                  padding: '8px',
                  backgroundColor: '#f3f4f6',
                  borderRadius: '4px',
                  fontSize: '11px',
                  overflow: 'auto'
                }}
              >
                {JSON.stringify(violation.context, null, 2)}
              </pre>
            </div>
          )}
          
          <div style={{ marginTop: '8px', fontSize: '12px', color: '#6b7280' }}>
            Règle: <strong>{violation.ruleName}</strong>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Filtre de sévérité
 */
const SeverityFilter = ({ selected, counts, onChange }) => (
  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
    <button
      onClick={() => onChange(null)}
      style={{
        padding: '6px 12px',
        borderRadius: '6px',
        border: selected === null ? '2px solid #3b82f6' : '1px solid #d1d5db',
        backgroundColor: selected === null ? '#eff6ff' : '#fff',
        cursor: 'pointer',
        fontSize: '13px',
        fontWeight: selected === null ? 600 : 400
      }}
    >
      Tous ({Object.values(counts).reduce((a, b) => a + b, 0)})
    </button>
    
    {Object.entries(SEVERITY_CONFIG).map(([key, config]) => (
      <button
        key={key}
        onClick={() => onChange(key)}
        style={{
          padding: '6px 12px',
          borderRadius: '6px',
          border: selected === key ? `2px solid ${config.color}` : '1px solid #d1d5db',
          backgroundColor: selected === key ? config.bgColor : '#fff',
          cursor: 'pointer',
          fontSize: '13px',
          fontWeight: selected === key ? 600 : 400,
          opacity: counts[key] === 0 ? 0.5 : 1
        }}
        disabled={counts[key] === 0}
      >
        {config.icon} {counts[key] || 0}
      </button>
    ))}
  </div>
);

/**
 * Liste des règles avec toggle
 */
const RulesList = ({ rules, onToggleRule }) => {
  const groupedRules = useMemo(() => {
    const groups = {};
    rules.forEach(rule => {
      const cat = rule.category;
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(rule);
    });
    return groups;
  }, [rules]);
  
  return (
    <div style={{ maxHeight: '400px', overflow: 'auto' }}>
      {Object.entries(groupedRules).map(([category, categoryRules]) => (
        <div key={category} style={{ marginBottom: '16px' }}>
          <h4 style={{ 
            fontSize: '12px', 
            fontWeight: 600, 
            color: '#6b7280',
            textTransform: 'uppercase',
            marginBottom: '8px',
            letterSpacing: '0.5px'
          }}>
            📁 {CATEGORY_LABELS[category] || category}
          </h4>
          
          {categoryRules.map(rule => (
            <div
              key={rule.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '8px 12px',
                backgroundColor: rule.enabled ? '#fff' : '#f9fafb',
                borderRadius: '6px',
                marginBottom: '4px',
                border: '1px solid #e5e7eb',
                opacity: rule.enabled ? 1 : 0.6
              }}
            >
              <input
                type="checkbox"
                checked={rule.enabled}
                onChange={() => onToggleRule(rule.id)}
                style={{ cursor: 'pointer' }}
              />
              
              <span>{SEVERITY_CONFIG[rule.severity]?.icon || '⚪'}</span>
              
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '13px', fontWeight: 500 }}>{rule.name}</div>
                <div style={{ fontSize: '11px', color: '#6b7280', fontFamily: 'monospace' }}>
                  {rule.erk}
                </div>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

// =============================================================================
// COMPOSANT PRINCIPAL
// =============================================================================

/**
 * MetaRulesAuditPanel - Panneau principal d'audit
 * 
 * @param {Object} props
 * @param {AuditResult} props.auditResult - Résultat de l'audit
 * @param {RuleInfo[]} props.rules - Liste des règles
 * @param {Function} props.onRunAudit - Callback pour relancer l'audit
 * @param {Function} props.onToggleRule - Callback pour activer/désactiver une règle
 * @param {Function} props.onObjectClick - Callback quand on clique sur un objet
 * @param {Function} props.onExport - Callback pour exporter le rapport
 */
const MetaRulesAuditPanel = ({
  auditResult,
  rules = [],
  onRunAudit,
  onToggleRule,
  onObjectClick,
  onExport
}) => {
  const [activeTab, setActiveTab] = useState('violations');
  const [severityFilter, setSeverityFilter] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Calcul des stats par sévérité
  const severityCounts = useMemo(() => {
    const counts = { critical: 0, error: 0, warning: 0, info: 0 };
    (auditResult?.errors || []).forEach(v => {
      counts[v.severity] = (counts[v.severity] || 0) + 1;
    });
    return counts;
  }, [auditResult]);
  
  // Filtrage des violations
  const filteredViolations = useMemo(() => {
    if (!auditResult?.errors) return [];
    
    let filtered = auditResult.errors;
    
    if (severityFilter) {
      filtered = filtered.filter(v => v.severity === severityFilter);
    }
    
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(v =>
        v.objectId.toLowerCase().includes(query) ||
        v.objectLineage.toLowerCase().includes(query) ||
        v.message.toLowerCase().includes(query) ||
        v.ruleId.toLowerCase().includes(query)
      );
    }
    
    // Tri par sévérité
    filtered.sort((a, b) => {
      return (SEVERITY_CONFIG[a.severity]?.order || 99) - (SEVERITY_CONFIG[b.severity]?.order || 99);
    });
    
    return filtered;
  }, [auditResult, severityFilter, searchQuery]);
  
  if (!auditResult) {
    return (
      <div style={{
        padding: '40px',
        textAlign: 'center',
        backgroundColor: '#f9fafb',
        borderRadius: '12px',
        border: '2px dashed #d1d5db'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
        <h3 style={{ margin: '0 0 8px', color: '#374151' }}>Aucun audit disponible</h3>
        <p style={{ color: '#6b7280', marginBottom: '16px' }}>
          Lancez un audit pour vérifier les MetaRules de structure.
        </p>
        {onRunAudit && (
          <button
            onClick={onRunAudit}
            style={{
              padding: '10px 20px',
              backgroundColor: '#3b82f6',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer'
            }}
          >
            🔍 Lancer l'audit
          </button>
        )}
      </div>
    );
  }
  
  return (
    <div style={{ fontFamily: 'system-ui, sans-serif' }}>
      {/* Header avec statut global */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          backgroundColor: auditResult.ok ? '#ecfdf5' : '#fef2f2',
          borderRadius: '12px',
          marginBottom: '20px',
          border: `2px solid ${auditResult.ok ? '#10b981' : '#ef4444'}`
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '32px' }}>{auditResult.ok ? '✅' : '❌'}</span>
          <div>
            <h2 style={{ margin: 0, fontSize: '18px', color: auditResult.ok ? '#065f46' : '#991b1b' }}>
              {auditResult.ok ? 'Audit OK' : 'Audit FAILED'}
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#6b7280' }}>
              {new Date(auditResult.timestamp).toLocaleString('fr-FR')}
            </p>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '8px' }}>
          {onExport && (
            <button
              onClick={onExport}
              style={{
                padding: '8px 16px',
                backgroundColor: '#fff',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '13px'
              }}
            >
              📥 Exporter
            </button>
          )}
          {onRunAudit && (
            <button
              onClick={onRunAudit}
              style={{
                padding: '8px 16px',
                backgroundColor: '#3b82f6',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: 500
              }}
            >
              🔄 Relancer
            </button>
          )}
        </div>
      </div>
      
      {/* Statistiques */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <StatCard
          label="Objets vérifiés"
          value={auditResult.stats?.objects_checked || 0}
          icon="📦"
          color="#3b82f6"
        />
        <StatCard
          label="Règles appliquées"
          value={auditResult.stats?.rules_applied || 0}
          icon="📏"
          color="#8b5cf6"
        />
        <StatCard
          label="Critiques"
          value={severityCounts.critical}
          icon="🔴"
          color="#dc2626"
        />
        <StatCard
          label="Erreurs"
          value={severityCounts.error}
          icon="🟠"
          color="#ea580c"
        />
        <StatCard
          label="Avertissements"
          value={severityCounts.warning}
          icon="🟡"
          color="#ca8a04"
        />
      </div>
      
      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px', borderBottom: '2px solid #e5e7eb' }}>
        {[
          { id: 'violations', label: 'Violations', count: auditResult.errors?.length || 0 },
          { id: 'rules', label: 'Règles', count: rules.length }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '10px 16px',
              backgroundColor: activeTab === tab.id ? '#fff' : 'transparent',
              border: 'none',
              borderBottom: activeTab === tab.id ? '2px solid #3b82f6' : '2px solid transparent',
              marginBottom: '-2px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: activeTab === tab.id ? 600 : 400,
              color: activeTab === tab.id ? '#1f2937' : '#6b7280'
            }}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>
      
      {/* Contenu des tabs */}
      {activeTab === 'violations' && (
        <div>
          {/* Filtres */}
          <div style={{ marginBottom: '16px' }}>
            <div style={{ marginBottom: '12px' }}>
              <SeverityFilter
                selected={severityFilter}
                counts={severityCounts}
                onChange={setSeverityFilter}
              />
            </div>
            
            <input
              type="text"
              placeholder="🔍 Rechercher par objet, règle, message..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
            />
          </div>
          
          {/* Liste des violations */}
          {filteredViolations.length === 0 ? (
            <div style={{
              padding: '40px',
              textAlign: 'center',
              backgroundColor: '#f9fafb',
              borderRadius: '8px'
            }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>✨</div>
              <p style={{ color: '#6b7280', margin: 0 }}>
                {auditResult.errors?.length === 0
                  ? 'Aucune violation détectée !'
                  : 'Aucune violation ne correspond aux filtres.'}
              </p>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '12px' }}>
                {filteredViolations.length} violation{filteredViolations.length > 1 ? 's' : ''} affichée{filteredViolations.length > 1 ? 's' : ''}
              </div>
              
              {filteredViolations.map((v, idx) => (
                <ViolationCard
                  key={`${v.objectId}-${v.ruleId}-${idx}`}
                  violation={v}
                  onObjectClick={onObjectClick}
                />
              ))}
            </div>
          )}
        </div>
      )}
      
      {activeTab === 'rules' && (
        <RulesList rules={rules} onToggleRule={onToggleRule} />
      )}
    </div>
  );
};

export default MetaRulesAuditPanel;
