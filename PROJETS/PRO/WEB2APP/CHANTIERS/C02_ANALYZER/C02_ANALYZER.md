# CHANTIER 02 — ANALYZER (Analyse IA de la structure)

⚠️ **CE PROJET N'UTILISE PAS EUREKAI**
Stack : Python + Claude API. Pas de GEV/ERK.

---

## OBJECTIF
Utiliser l'IA (Claude) pour analyser le site parsé et comprendre sa structure sémantique : identifier les composants, les patterns UI, la hiérarchie des écrans.

## PRÉREQUIS
- Livrables C01 (parser/) : ParsedSite avec l'arbre DOM

## INPUTS
```python
ParsedSite  # Du C01
```

## OUTPUTS
```python
@dataclass
class AnalyzedSite:
    screens: list[Screen]           # Écrans identifiés
    components: list[Component]     # Composants réutilisables
    design_system: DesignSystem     # Couleurs, typo, spacing
    navigation_structure: NavStructure
    user_flows: list[UserFlow]
```

---

## STRUCTURE DE FICHIERS

```
backend/app/analyzer/
├── __init__.py
├── models.py           # Dataclasses
├── claude_client.py    # Client Claude API
├── structure_analyzer.py   # Analyse structure
├── component_detector.py   # Détection composants
├── design_extractor.py     # Extraction design system
├── prompts/
│   ├── analyze_page.txt
│   ├── detect_components.txt
│   └── extract_design.txt
└── service.py
```

---

## MODÈLES DE DONNÉES

### models.py

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class ScreenType(Enum):
    HOME = "home"
    LIST = "list"              # Liste d'items
    DETAIL = "detail"          # Page détail
    FORM = "form"              # Formulaire
    AUTH = "auth"              # Login/Register
    DASHBOARD = "dashboard"
    SETTINGS = "settings"
    PROFILE = "profile"
    LANDING = "landing"
    ERROR = "error"
    OTHER = "other"

class ComponentType(Enum):
    HEADER = "header"
    FOOTER = "footer"
    NAVBAR = "navbar"
    SIDEBAR = "sidebar"
    HERO = "hero"
    CARD = "card"
    BUTTON = "button"
    INPUT = "input"
    FORM = "form"
    LIST = "list"
    GRID = "grid"
    MODAL = "modal"
    TABS = "tabs"
    ACCORDION = "accordion"
    CAROUSEL = "carousel"
    AVATAR = "avatar"
    BADGE = "badge"
    MENU = "menu"
    DROPDOWN = "dropdown"
    TOAST = "toast"
    CUSTOM = "custom"

@dataclass
class Component:
    id: str
    name: str                           # Ex: "ProductCard"
    type: ComponentType
    description: str
    source_element_ids: list[str]       # IDs des éléments source
    props: list[dict] = field(default_factory=list)  # {name, type, required}
    variants: list[str] = field(default_factory=list)
    reuse_count: int = 1                # Nombre d'occurrences
    suggested_native: str = ""          # Composant RN suggéré

@dataclass
class Screen:
    id: str
    name: str                           # Ex: "HomePage", "ProductDetail"
    path: str                           # /home, /product/:id
    type: ScreenType
    source_page_url: str
    components: list[str] = field(default_factory=list)  # IDs des composants
    params: list[str] = field(default_factory=list)      # Paramètres dynamiques
    description: str = ""

@dataclass 
class ColorToken:
    name: str               # primary, secondary, background
    value: str              # #8b5cf6
    usage: str              # "Boutons principaux"

@dataclass
class TypographyToken:
    name: str               # h1, body, caption
    font_family: str
    font_size: str
    font_weight: str
    line_height: Optional[str] = None
    usage: str = ""

@dataclass
class SpacingToken:
    name: str               # xs, sm, md, lg, xl
    value: int              # En pixels
    
@dataclass
class DesignSystem:
    colors: list[ColorToken] = field(default_factory=list)
    typography: list[TypographyToken] = field(default_factory=list)
    spacing: list[SpacingToken] = field(default_factory=list)
    border_radius: dict = field(default_factory=dict)  # sm, md, lg, full
    shadows: list[dict] = field(default_factory=list)

@dataclass
class NavItem:
    label: str
    path: str
    icon: Optional[str] = None
    children: list["NavItem"] = field(default_factory=list)

@dataclass
class NavStructure:
    type: str                           # tabs, drawer, stack, bottom-tabs
    items: list[NavItem] = field(default_factory=list)
    has_auth_flow: bool = False
    auth_screens: list[str] = field(default_factory=list)

@dataclass
class UserFlow:
    name: str                           # "Checkout", "Onboarding"
    steps: list[str]                    # Liste d'écrans
    entry_point: str
    exit_points: list[str] = field(default_factory=list)

@dataclass
class AnalyzedSite:
    source_url: str
    screens: list[Screen] = field(default_factory=list)
    components: list[Component] = field(default_factory=list)
    design_system: DesignSystem = field(default_factory=DesignSystem)
    navigation: NavStructure = field(default_factory=NavStructure)
    user_flows: list[UserFlow] = field(default_factory=list)
    analysis_notes: list[str] = field(default_factory=list)
```

---

## CLIENT CLAUDE

### claude_client.py

```python
import anthropic
from typing import Optional
import json

class ClaudeClient:
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    async def analyze(self, prompt: str, system: str = "") -> str:
        """Envoie une requête à Claude."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    
    async def analyze_json(self, prompt: str, system: str = "") -> dict:
        """Envoie une requête et parse la réponse JSON."""
        response = await self.analyze(prompt, system)
        
        # Extraire le JSON de la réponse
        try:
            # Chercher un bloc JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            
            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": response}
```

---

## PROMPTS

### prompts/analyze_page.txt

```
Tu es un expert en analyse d'interfaces utilisateur web.

Analyse cette page web et identifie :
1. Le TYPE d'écran (home, list, detail, form, auth, dashboard, etc.)
2. Les COMPOSANTS présents (header, hero, cards, forms, etc.)
3. La HIÉRARCHIE visuelle
4. Les INTERACTIONS possibles

PAGE À ANALYSER :
URL: {url}
Titre: {title}

STRUCTURE DOM (simplifiée) :
{dom_tree}

STYLES PRINCIPAUX :
{main_styles}

Réponds en JSON avec cette structure :
```json
{
  "screen_type": "home|list|detail|form|auth|dashboard|other",
  "screen_name": "NomDeLEcran",
  "description": "Description courte",
  "components": [
    {
      "type": "header|hero|card|form|...",
      "name": "NomComposant",
      "element_ids": ["id1", "id2"],
      "description": "Ce que fait ce composant"
    }
  ],
  "interactions": ["click sur X", "scroll", "form submit"],
  "params": ["id", "slug"] // Si page dynamique
}
```
```

### prompts/detect_components.txt

```
Tu es un expert en design systems et composants UI.

Analyse ces éléments et identifie les COMPOSANTS RÉUTILISABLES.
Un composant réutilisable apparaît plusieurs fois avec des variations mineures.

ÉLÉMENTS :
{elements}

Pour chaque composant identifié, détermine :
1. Son NOM (PascalCase, ex: ProductCard)
2. Son TYPE (card, button, input, list, etc.)
3. Ses PROPS (propriétés variables entre instances)
4. Ses VARIANTES (si applicable)
5. Le composant REACT NATIVE équivalent suggéré

Réponds en JSON :
```json
{
  "components": [
    {
      "name": "ProductCard",
      "type": "card",
      "description": "Carte produit avec image, titre, prix",
      "element_ids": ["elem1", "elem2", "elem3"],
      "props": [
        {"name": "image", "type": "string", "required": true},
        {"name": "title", "type": "string", "required": true},
        {"name": "price", "type": "number", "required": true},
        {"name": "onPress", "type": "function", "required": false}
      ],
      "variants": ["default", "compact", "featured"],
      "suggested_native": "TouchableOpacity > Image + Text"
    }
  ]
}
```
```

### prompts/extract_design.txt

```
Tu es un expert en design systems.

Analyse ces styles extraits d'un site web et crée un DESIGN SYSTEM normalisé.

COULEURS TROUVÉES :
{colors}

FONTS TROUVÉES :
{fonts}

STYLES COMPUTED :
{styles}

Crée un design system avec :
1. COULEURS nommées (primary, secondary, background, text, etc.)
2. TYPOGRAPHIE (h1-h6, body, caption, etc.)
3. SPACING (xs, sm, md, lg, xl en pixels)
4. BORDER RADIUS
5. SHADOWS

Réponds en JSON :
```json
{
  "colors": [
    {"name": "primary", "value": "#8b5cf6", "usage": "Boutons, liens"},
    {"name": "background", "value": "#ffffff", "usage": "Fond principal"}
  ],
  "typography": [
    {"name": "h1", "fontFamily": "Inter", "fontSize": "36px", "fontWeight": "700"},
    {"name": "body", "fontFamily": "Inter", "fontSize": "16px", "fontWeight": "400"}
  ],
  "spacing": [
    {"name": "xs", "value": 4},
    {"name": "sm", "value": 8},
    {"name": "md", "value": 16},
    {"name": "lg", "value": 24},
    {"name": "xl", "value": 32}
  ],
  "borderRadius": {
    "sm": "4px",
    "md": "8px",
    "lg": "16px",
    "full": "9999px"
  },
  "shadows": [
    {"name": "sm", "value": "0 1px 2px rgba(0,0,0,0.05)"},
    {"name": "md", "value": "0 4px 6px rgba(0,0,0,0.1)"}
  ]
}
```
```

---

## ANALYSEURS

### structure_analyzer.py

```python
from .models import Screen, ScreenType, AnalyzedSite
from .claude_client import ClaudeClient
from ..parser.models import ParsedSite, ParsedPage, ParsedElement
from pathlib import Path

class StructureAnalyzer:
    def __init__(self, claude_client: ClaudeClient):
        self.claude = claude_client
        self.prompts_dir = Path(__file__).parent / "prompts"
    
    async def analyze_site(self, parsed_site: ParsedSite) -> list[Screen]:
        """Analyse toutes les pages et identifie les écrans."""
        screens = []
        
        for page in parsed_site.pages:
            screen = await self.analyze_page(page)
            screens.append(screen)
        
        return screens
    
    async def analyze_page(self, page: ParsedPage) -> Screen:
        """Analyse une page individuelle."""
        # Préparer le prompt
        prompt_template = self._load_prompt("analyze_page.txt")
        
        dom_tree = self._simplify_dom_tree(page.root_element)
        main_styles = self._extract_main_styles(page.root_element)
        
        prompt = prompt_template.format(
            url=page.url,
            title=page.title,
            dom_tree=dom_tree,
            main_styles=main_styles
        )
        
        # Appeler Claude
        result = await self.claude.analyze_json(prompt)
        
        # Convertir en Screen
        screen = Screen(
            id=self._generate_id(page.path),
            name=result.get("screen_name", "Unknown"),
            path=page.path,
            type=self._parse_screen_type(result.get("screen_type", "other")),
            source_page_url=page.url,
            description=result.get("description", ""),
            params=result.get("params", [])
        )
        
        return screen
    
    def _simplify_dom_tree(self, element: ParsedElement, depth: int = 0, max_depth: int = 5) -> str:
        """Simplifie l'arbre DOM pour le prompt."""
        if not element or depth > max_depth:
            return ""
        
        indent = "  " * depth
        tag = element.tag
        classes = ".".join(element.classes[:3]) if element.classes else ""
        text = f'"{element.text_content[:50]}..."' if element.text_content else ""
        
        line = f"{indent}<{tag}"
        if classes:
            line += f" class='{classes}'"
        if text:
            line += f"> {text}"
        else:
            line += ">"
        
        lines = [line]
        
        for child in element.children[:10]:  # Limite les enfants
            child_tree = self._simplify_dom_tree(child, depth + 1, max_depth)
            if child_tree:
                lines.append(child_tree)
        
        return "\n".join(lines)
    
    def _extract_main_styles(self, element: ParsedElement) -> str:
        """Extrait les styles principaux."""
        styles = []
        
        def collect_styles(el: ParsedElement, depth: int = 0):
            if depth > 3:
                return
            if el.styles:
                s = el.styles
                style_str = f"{el.tag}: "
                parts = []
                if s.display and s.display != "block":
                    parts.append(f"display:{s.display}")
                if s.background_color and s.background_color != "rgba(0, 0, 0, 0)":
                    parts.append(f"bg:{s.background_color}")
                if s.color:
                    parts.append(f"color:{s.color}")
                if s.font_size:
                    parts.append(f"font:{s.font_size}")
                if parts:
                    styles.append(style_str + ", ".join(parts))
            
            for child in el.children[:5]:
                collect_styles(child, depth + 1)
        
        collect_styles(element)
        return "\n".join(styles[:20])
    
    def _parse_screen_type(self, type_str: str) -> ScreenType:
        """Parse le type d'écran."""
        mapping = {
            "home": ScreenType.HOME,
            "list": ScreenType.LIST,
            "detail": ScreenType.DETAIL,
            "form": ScreenType.FORM,
            "auth": ScreenType.AUTH,
            "dashboard": ScreenType.DASHBOARD,
            "settings": ScreenType.SETTINGS,
            "profile": ScreenType.PROFILE,
            "landing": ScreenType.LANDING,
            "error": ScreenType.ERROR,
        }
        return mapping.get(type_str.lower(), ScreenType.OTHER)
    
    def _generate_id(self, path: str) -> str:
        """Génère un ID depuis le path."""
        import hashlib
        return hashlib.md5(path.encode()).hexdigest()[:8]
    
    def _load_prompt(self, filename: str) -> str:
        """Charge un template de prompt."""
        filepath = self.prompts_dir / filename
        with open(filepath, "r") as f:
            return f.read()
```

### component_detector.py

```python
from .models import Component, ComponentType
from .claude_client import ClaudeClient
from ..parser.models import ParsedElement
from pathlib import Path
import json

class ComponentDetector:
    def __init__(self, claude_client: ClaudeClient):
        self.claude = claude_client
        self.prompts_dir = Path(__file__).parent / "prompts"
    
    async def detect_components(self, elements: list[ParsedElement]) -> list[Component]:
        """Détecte les composants réutilisables."""
        # Préparer les éléments pour le prompt
        elements_summary = self._summarize_elements(elements)
        
        # Charger le prompt
        prompt_template = self._load_prompt("detect_components.txt")
        prompt = prompt_template.format(elements=elements_summary)
        
        # Appeler Claude
        result = await self.claude.analyze_json(prompt)
        
        # Convertir en Components
        components = []
        for c in result.get("components", []):
            component = Component(
                id=self._generate_id(c.get("name", "")),
                name=c.get("name", "Unknown"),
                type=self._parse_component_type(c.get("type", "custom")),
                description=c.get("description", ""),
                source_element_ids=c.get("element_ids", []),
                props=c.get("props", []),
                variants=c.get("variants", []),
                suggested_native=c.get("suggested_native", "")
            )
            components.append(component)
        
        return components
    
    def _summarize_elements(self, elements: list[ParsedElement]) -> str:
        """Résume les éléments pour le prompt."""
        summaries = []
        
        for el in elements[:50]:  # Limite
            summary = {
                "id": el.id,
                "tag": el.tag,
                "classes": el.classes[:5],
                "text": el.text_content[:100] if el.text_content else None,
                "children_count": len(el.children),
                "has_click": el.has_click_handler
            }
            summaries.append(summary)
        
        return json.dumps(summaries, indent=2)
    
    def _parse_component_type(self, type_str: str) -> ComponentType:
        """Parse le type de composant."""
        mapping = {
            "header": ComponentType.HEADER,
            "footer": ComponentType.FOOTER,
            "navbar": ComponentType.NAVBAR,
            "sidebar": ComponentType.SIDEBAR,
            "hero": ComponentType.HERO,
            "card": ComponentType.CARD,
            "button": ComponentType.BUTTON,
            "input": ComponentType.INPUT,
            "form": ComponentType.FORM,
            "list": ComponentType.LIST,
            "grid": ComponentType.GRID,
            "modal": ComponentType.MODAL,
            "tabs": ComponentType.TABS,
            "accordion": ComponentType.ACCORDION,
            "carousel": ComponentType.CAROUSEL,
            "avatar": ComponentType.AVATAR,
            "badge": ComponentType.BADGE,
            "menu": ComponentType.MENU,
            "dropdown": ComponentType.DROPDOWN,
        }
        return mapping.get(type_str.lower(), ComponentType.CUSTOM)
    
    def _generate_id(self, name: str) -> str:
        import hashlib
        return hashlib.md5(name.encode()).hexdigest()[:8]
    
    def _load_prompt(self, filename: str) -> str:
        filepath = self.prompts_dir / filename
        with open(filepath, "r") as f:
            return f.read()
```

---

## SERVICE

### service.py

```python
from .models import AnalyzedSite, NavStructure, NavItem
from .claude_client import ClaudeClient
from .structure_analyzer import StructureAnalyzer
from .component_detector import ComponentDetector
from .design_extractor import DesignExtractor
from ..parser.models import ParsedSite

class AnalyzerService:
    def __init__(self, api_key: str = None):
        self.claude = ClaudeClient(api_key=api_key)
        self.structure_analyzer = StructureAnalyzer(self.claude)
        self.component_detector = ComponentDetector(self.claude)
        self.design_extractor = DesignExtractor(self.claude)
    
    async def analyze(self, parsed_site: ParsedSite) -> AnalyzedSite:
        """Analyse complète d'un site parsé."""
        
        # 1. Analyser la structure (écrans)
        screens = await self.structure_analyzer.analyze_site(parsed_site)
        
        # 2. Détecter les composants
        all_elements = self._collect_all_elements(parsed_site)
        components = await self.component_detector.detect_components(all_elements)
        
        # 3. Extraire le design system
        design_system = await self.design_extractor.extract(parsed_site)
        
        # 4. Analyser la navigation
        navigation = self._analyze_navigation(parsed_site, screens)
        
        # 5. Assembler le résultat
        analyzed = AnalyzedSite(
            source_url=parsed_site.url,
            screens=screens,
            components=components,
            design_system=design_system,
            navigation=navigation
        )
        
        return analyzed
    
    def _collect_all_elements(self, parsed_site: ParsedSite) -> list:
        """Collecte tous les éléments de toutes les pages."""
        elements = []
        
        for page in parsed_site.pages:
            if page.root_element:
                elements.extend(self._flatten_elements(page.root_element))
        
        return elements
    
    def _flatten_elements(self, element, result=None):
        """Aplatit l'arbre d'éléments."""
        if result is None:
            result = []
        
        result.append(element)
        for child in element.children:
            self._flatten_elements(child, result)
        
        return result
    
    def _analyze_navigation(self, parsed_site: ParsedSite, screens: list) -> NavStructure:
        """Détermine la structure de navigation."""
        # Logique simplifiée
        nav_items = []
        
        for page in parsed_site.pages:
            nav_items.append(NavItem(
                label=page.title or page.path,
                path=page.path
            ))
        
        # Déterminer le type de nav
        nav_type = "stack"
        if len(screens) <= 5:
            nav_type = "bottom-tabs"
        elif any(s.type.value == "auth" for s in screens):
            nav_type = "stack"  # Auth nécessite stack
        
        return NavStructure(
            type=nav_type,
            items=nav_items,
            has_auth_flow=any(s.type.value == "auth" for s in screens)
        )
```

---

## LIVRABLES

```
backend/app/analyzer/
├── __init__.py
├── models.py
├── claude_client.py
├── structure_analyzer.py
├── component_detector.py
├── design_extractor.py
├── service.py
└── prompts/
    ├── analyze_page.txt
    ├── detect_components.txt
    └── extract_design.txt

tests/
└── test_analyzer.py
```

## CRITÈRES DE VALIDATION

- [ ] Identifie correctement les types d'écrans
- [ ] Détecte les composants réutilisables
- [ ] Extrait un design system cohérent
- [ ] Détermine la structure de navigation
- [ ] Fonctionne avec Claude API
- [ ] Tests passent

## TEMPS ESTIMÉ
4 heures
