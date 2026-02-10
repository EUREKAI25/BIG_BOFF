# WEB2APP — PLAN D'EXÉCUTION

## TABLEAU DE LANCEMENT

| Chantier | Step | Prérequis | Durée |
|----------|------|-----------|-------|
| **C01** Parser | 1 | ∅ | 3h |
| **C03** Mapper | 1 | ∅ | 4h |
| **C05** Native Components | 1 | ∅ | 6h |
| **C02** Analyzer | 2 | C01 | 4h |
| **C06** Navigation | 2 | C02 | 3h |
| **C07** Assets | 2 | C01 | 2h |
| **C04** Generator | 3 | C02, C03 | 5h |
| **C08** Preview | 4 | C04, C05 | 4h |
| **C09** API Backend | 5 | C01-C08 | 4h |
| **C10** Frontend | 6 | C09 | 4h |
| **C11** Deploy | 6 | C09, C10 | 2h |
| **C00** Final Assembly | 7 | TOUS | 3h |

---

## DIAGRAMME DE DÉPENDANCES

```
STEP 1 (parallèle) :
    C01 Parser ════════════╗
    C03 Mapper ════════════╬═══════════════════════════════╗
    C05 Native Components ═╩═══════════════════════╗       ║
                                                   ║       ║
STEP 2 (après C01) :                               ║       ║
    C02 Analyzer ◄── C01                           ║       ║
    C06 Navigation ◄── C02                         ║       ║
    C07 Assets ◄── C01                             ║       ║
                                                   ║       ║
STEP 3 :                                           ║       ║
    C04 Generator ◄── C02 + C03 ◄══════════════════╩═══════╝
                                                   
STEP 4 :                                           
    C08 Preview ◄── C04 + C05                      
                                                   
STEP 5 :                                           
    C09 API ◄── C01-C08                            
                                                   
STEP 6 (parallèle) :                               
    C10 Frontend ◄── C09                           
    C11 Deploy ◄── C09                             
                                                   
STEP 7 :                                           
    C00 Final Assembly ◄── TOUS                    
```

---

## CHECKLIST PAR AGENT

### Agent 1 — Core Engine
```
□ C01 Parser (3h)
□ C02 Analyzer (4h)
□ C04 Generator (5h)
Total : 12h
```

### Agent 2 — Components & Navigation
```
□ C05 Native Components (6h)
□ C06 Navigation (3h)
□ C08 Preview (4h)
Total : 13h
```

### Agent 3 — Rules & Assets
```
□ C03 Mapper (4h)
□ C07 Assets (2h)
□ C09 API (4h)
Total : 10h
```

### Agent 4 — Frontend & Deploy
```
□ C10 Frontend (4h)
□ C11 Deploy (2h)
□ C00 Final Assembly (3h)
Total : 9h
```

---

## TEMPS ESTIMÉS

| Mode | Durée |
|------|-------|
| 1 agent (séquentiel) | ~44h |
| 2 agents | ~25h |
| 3 agents | ~18h |
| 4 agents | ~15h |

---

## POUR LANCER CHAQUE CHANTIER

### C01 Parser
```
Donner : C01_PARSER.md
Prérequis : Aucun
```

### C02 Analyzer
```
Donner : C02_ANALYZER.md
Prérequis : Livrables C01 (parser/)
```

### C03 Mapper
```
Donner : C03_MAPPER.md
Prérequis : Aucun
```

### C04 Generator
```
Donner : C04_GENERATOR.md
Prérequis : Livrables C02 + C03
```

### C05 Native Components
```
Donner : C05_NATIVE_COMPONENTS.md
Prérequis : Aucun
```

### C06 Navigation
```
Donner : C06_NAVIGATION.md
Prérequis : Livrables C02
```

### C07 Assets
```
Donner : C07_ASSETS.md
Prérequis : Livrables C01
```

### C08 Preview
```
Donner : C08_PREVIEW.md
Prérequis : Livrables C04 + C05
```

### C09 API
```
Donner : C09_API.md
Prérequis : Livrables C01-C08
```

### C10 Frontend
```
Donner : C10_FRONTEND.md
Prérequis : Livrables C09
```

### C11 Deploy
```
Donner : C11_DEPLOY.md
Prérequis : Livrables C09 + C10
```

### C00 Final Assembly
```
Donner : C00_FINAL_ASSEMBLY.md
Prérequis : TOUS les livrables
Exécuter : ./build.sh
```
