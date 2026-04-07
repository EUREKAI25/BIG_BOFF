# Eurkai — Schemas, Vectors, Endpoints (recap fixé)

> Périmètre : cette note récapitule **uniquement** ce qui a été fixé pendant l’échange, après digressions.
> Sujet initial : **schemas / héritage / templates**, puis clarification sur **vectors**, **modes**, **endpoints**, **polling**.

---

## 1) Schéma fractal universel

### 1.1 Structure racine (invariant)
Tout objet suit :

- `object`
  - `elementlist`
    - `baseelementlist`
      - `attributelist`
      - `methodlist`
      - `optionlist`
      - `rulelist`
      - `treelist`
        - `childrenlist`
        - `parentlist`
        - `siblinglist`

Chaque liste porte à son tour (même structure fractale) :

- `owned_element_list`
- `injected_element_list`
- `inherited_element_list`

### 1.2 Priorité de résolution (invariant)
Règle universelle (fixée) :

- **owned > injected > inherited**

Aucune inversion ad hoc. Les mécanismes d’exception passent par des **overrides injectés** (ex : ORSEC) avec **durée de vie limitée** (TTL), renouvelable.

### 1.3 Baseelementlist (champs universels)
La `baseelementlist` contient les attributs présents “partout” (liste non exhaustive, mais fixée dans l’échange) :

- `ident`, `name`, `description`
- `version`, `status`, `lineage`, `vector_ident` (ou `vector_id` si choisi plus tard)
- `create_date`, `create_user`, `last_update_date`, `last_update_user`
- `create_prompt_template`, `validate_prompt_template` (hérités au niveau racine)

---

## 2) Templates

### 2.1 Principe
- Un objet est créé/validé à partir de **son schema** et **son template** s’il en a.
- Tout template est **récursif**, car il hérite d'Object et doit s’adapter à la structure fractale.

### 2.2 Sélection de template
- `Object.template` = mécanisme de résolution du template actif
- `Object.template.optionlist` = options disponibles quand plusieurs templates existent
- `Object.template.rule_list.policy_list.selection_policy` = politique de sélection

---

## 3) Vectors : objets, modes, payload

### 3.1 Vector est un Object
- Un `Vector` est un `Object`, donc on peut écrire :
  - `vector.mode`
  - `vector.payload_element_list`
  - `vector.rule_list`, etc.

### 3.2 Modes (valeurs uniques et rôle unique)
Fixé :
- `mode ∈ {active, passive, reactive}`
- **Le mode sert uniquement à imposer/injecter ses règles** (aucun autre rôle).
- Pas de logique “if …” : les règles sont **portées/injectées** par l’objet mode.

### 3.3 Comparaison pour plug (interne)
Fixé :
- Le plug se valide par comparaison de payloads **via des objets Vector** :

**Interne (Eurkai ↔ Eurkai)**  
- `ActiveVector.payload_element_list`
vs
- `XVector.payload_element_list`  
où `XVector` est un objet concret, ex : `BriefVector`, `VisitorVector`, etc.

> (On a abandonné la logique male/female.)

### 3.4 Externe (chaîne MetaPatch) — mention sans détailler
Fixé comme principe (détaillé plus tard) :
- `APIEndpointOutput` → `PatchVector` → `ExternalObjectVector` → `XVector` (canonique Eurkai)
Puis validation interne : `ActiveVector ⇄ XVector`

---

## 4) Endpoints : choix “proche du code habituel”

### 4.1 Endpoints partout, même en interne
Fixé :
- Toutes les méthodes sont des **endpoints** (publics ou non selon permissions).
- Même en interne, on raisonne “endpoint”.

### 4.2 Ne pas utiliser `Endpoint.method`
Fixé :
- Pas `Endpoint.method = GET|POST|...` (car `method` existe déjà).
- On utilise des types d’endpoints :
  - `Endpoint:GETEndpoint`
  - `Endpoint:POSTEndpoint`
  - (éventuellement plus tard : `Endpoint:DELETEEndpoint`, etc.)

### 4.3 GET/POST et “CRUDOC”
Clarification fixée :
- `PUT/PATCH/DELETE` sont **surtout sémantiques** dans HTTP (pas un protocole différent).
- **Décision** : conserver l’angle “endpoint GET/POST” (proche du code habituel).
- CRUDOC peut exister comme logique interne, mais **si l’objectif est l’exposition publique**, on garde les endpoints HTTP (ou leurs types) comme vocabulaire principal.

---

## 5) Reactive + GET = Polling (connecté à Pulse)

### 5.1 Définition
Fixé :
- **Polling** = demander régulièrement “as-tu du nouveau ?”
- Reactive + GET = polling
- Polling est **connecté au Pulse**, ce qui est indispensable pour Cron.

### 5.2 Format de sortie
Fixé :
- output = `trigger_list` (format standard conservé)

---

## 6) Sécurité : token obligatoire (à inclure dès maintenant)

Fixé (mention) :
- Tous les appels incluent un token portant une `secretkey` — **même internes**.
- Les permissions détermineront l’accessibilité des endpoints (à traiter dans la section sécurité plus tard).

---

## 7) Cache (cache-first + updates)

### 7.1 Cache-first
Fixé :
- `inherited` est majoritairement cacheable (héritage stable)
- `injected` souvent cacheable aussi
- stratégie : **cache-first**, puis application des overrides `owned`/session

### 7.2 Updates “à appliquer”
Fixé :
- On stocke pendant la session les updates à appliquer au prochain chargement/commit.
- Règle importante : **jamais de solution hardcodée**  
  → on cible un **type** (`Storage`) et `Storage` choisit l’implémentation (bdd/cache/env/etc.) selon policy.

### 7.3 Actualisation selon exigence
Fixé :
- selon le niveau d’exigence, on peut décider d’actualiser le cache avant usage.

---

## 8) Glossaire minimal (termes utilisés)

- **ActiveVector** : décrit “où on est” (contexte de validation/exécution) et expose `payload_element_list`.
- **XVector** : vector concret (BriefVector, VisitorVector, etc.) exposant `payload_element_list`.
- **trigger_list** : format de sortie pour reactive/polling.
- **Endpoint:GETEndpoint / Endpoint:POSTEndpoint** : types d’endpoints (internes ou publics).

---

## 9) Ce qui reste explicitement “à traiter plus tard”
- Détails MetaPatch / objets externes (APIEndpointOutput → Patch → ExternalObjectVector…)
- Formalisation complète des policies de cache (TTL, invalidations, etc.)
- Spécification sécurité complète (token structure, scopes, secretkey, rotation, etc.)
- Définition complète des schemas de planes/layers (identity/context/view/cache masks) si nécessaire
