# EURKAI — architecture minimale (catalogs + instances)
# (templates + schemas dynamiques → manifests only, overrides optionnels)

ROOT/
├── catalogs/                         # définitions de TYPES (pas d'instances)
│   ├── entity/
│   │   └── agent/
│   │       ├── Agent/
│   │       │   └── manifest.json
│   │       ├── AIAgent/
│   │       │   └── manifest.json     # extends: entity.agent.Agent
│   │       └── OrchestrateAgent/
│   │           └── manifest.json     # extends: entity.agent.AIAgent
│   ├── core/
│   │   ├── function/
│   │   │   └── <FunctionType>/manifest.json
│   │   ├── method/
│   │   │   └── <MethodType>/manifest.json
│   │   ├── scenario/
│   │   │   └── <ScenarioType>/manifest.json
│   │   ├── input/
│   │   │   └── <InputType>/manifest.json
│   │   └── template/                 # optionnel (si tu catalogues des "template types")
│   │       └── <TemplateType>/manifest.json
│   ├── domain/                        # EURKAI métier (valeur)
│   │   ├── product/
│   │   │   └── <ProductType>/manifest.json
│   │   ├── service/
│   │   │   └── <ServiceType>/manifest.json
│   │   └── price/
│   │       └── <PriceType>/manifest.json
│   ├── governance/                    # auth/roles/permissions/rules/policies
│   │   ├── auth/
│   │   │   └── <AuthType>/manifest.json
│   │   ├── role/
│   │   │   └── <RoleType>/manifest.json
│   │   ├── permission/
│   │   │   └── <PermissionType>/manifest.json
│   │   ├── policy/
│   │   │   └── <PolicyType>/manifest.json
│   │   └── rule/
│   │       └── <RuleType>/manifest.json
│   ├── flow/                          # orchestration & temps
│   │   ├── event/
│   │   │   └── <EventType>/manifest.json
│   │   ├── process/
│   │   │   └── <ProcessType>/manifest.json
│   │   ├── hook/
│   │   │   └── <HookType>/manifest.json
│   │   └── cron/
│   │       └── <CronType>/manifest.json
│   ├── interface/                     # exposition & accès (+ registries)
│   │   ├── api/
│   │   │   └── <ApiType>/manifest.json
│   │   ├── endpoint/
│   │   │   └── <EndpointType>/manifest.json
│   │   ├── adapter/
│   │   │   └── <AdapterType>/manifest.json
│   │   └── catalog/                   # optionnel: types de catalog/registry eux-mêmes
│   │       └── <CatalogType>/manifest.json
│   ├── system/                        # infra & runtime
│   │   ├── server/
│   │   │   └── <ServerType>/manifest.json
│   │   ├── path/
│   │   │   └── <PathType>/manifest.json
│   │   └── storage/
│   │       └── <StorageType>/manifest.json
│   ├── config/                        # contexte + méta (profils, schémas dynamiques)
│   │   ├── context/
│   │   │   └── <ContextType>/manifest.json
│   │   └── meta/
│   │       └── <MetaType>/manifest.json
│   └── util/                          # helpers génériques (si tu veux les cataloguer)
│       └── <UtilType>/manifest.json
│
├── instances/                         # objets CONCRETS (données, états, historiques)
│   ├── entity/
│   │   └── agent/
│   │       ├── agent_001.json         # type: entity.agent.OrchestrateAgent
│   │       ├── agent_002.json         # type: entity.agent.AIAgent
│   │       └── agent_003.json         # type: entity.agent.Agent
│   ├── domain/
│   │   ├── product/
│   │   │   └── product_001.json       # type: domain.product.<ProductType>
│   │   ├── service/
│   │   │   └── service_001.json
│   │   └── price/
│   │       └── price_001.json
│   ├── governance/
│   │   ├── role/
│   │   │   └── role_admin.json
│   │   ├── permission/
│   │   │   └── perm_read.json
│   │   ├── policy/
│   │   │   └── policy_default.json
│   │   └── rule/
│   │       └── rule_tax_it_2026.json
│   ├── flow/
│   │   ├── event/
│   │   │   └── event_20260210_001.json
│   │   ├── process/
│   │   │   └── process_001.json
│   │   ├── hook/
│   │   │   └── hook_after_create_project.json
│   │   └── cron/
│   │       └── cron_dispatcher_minutely.json
│   ├── interface/
│   │   ├── endpoint/
│   │   │   └── endpoint_auth_login.json
│   │   └── adapter/
│   │       └── adapter_brevo.json
│   ├── system/
│   │   ├── server/
│   │   │   └── server_local_ionos.json
│   │   ├── path/
│   │   │   └── path_dropbox_bigboff.json
│   │   └── storage/
│   │       └── storage_postgres_main.json
│   └── config/
│       ├── context/
│       │   └── context_current.json
│       └── meta/
│           └── meta_standards_v1.json
│
