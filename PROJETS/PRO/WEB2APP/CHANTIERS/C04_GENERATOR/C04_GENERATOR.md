# CHANTIER 04 — GENERATOR (Génération code React Native)

⚠️ **CE PROJET N'UTILISE PAS EUREKAI**
Stack : Python + Jinja2 templates. Pas de GEV/ERK.

---

## OBJECTIF
Générer le code React Native complet à partir des éléments mappés : composants TSX, StyleSheets, structure de projet Expo.

## PRÉREQUIS
- C02 Analyzer (AnalyzedSite)
- C03 Mapper (MappingResult)

## OUTPUTS
```
expo-app/
├── app/                    # Expo Router pages
├── components/             # Composants générés
├── styles/                 # Theme et styles
└── package.json
```

---

## STRUCTURE

```
backend/app/generator/
├── __init__.py
├── models.py
├── code_generator.py       # Génère les fichiers TSX
├── style_generator.py      # Génère les StyleSheets
├── project_generator.py    # Structure projet Expo
├── templates/
│   ├── component.tsx.j2
│   ├── screen.tsx.j2
│   ├── stylesheet.ts.j2
│   └── package.json.j2
└── service.py
```

---

## TEMPLATES

### templates/component.tsx.j2

```typescript
{% raw %}
import React from 'react';
import { {{ imports | join(', ') }} } from 'react-native';
{% for extra in extra_imports %}
import {{ extra.default }} from '{{ extra.from }}';
{% endfor %}
import { styles } from './{{ name }}.styles';

{% if props %}
interface {{ name }}Props {
{% for prop in props %}
  {{ prop.name }}{% if not prop.required %}?{% endif %}: {{ prop.type }};
{% endfor %}
}
{% endif %}

export function {{ name }}({% if props %}{ {{ props | map(attribute='name') | join(', ') }} }: {{ name }}Props{% endif %}) {
  return (
{{ jsx_tree | indent(4, true) }}
  );
}
{% endraw %}
```

### templates/screen.tsx.j2

```typescript
{% raw %}
import React from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
{% for component in components %}
import { {{ component }} } from '@/components/{{ component }}';
{% endfor %}

export default function {{ name }}Screen() {
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
{{ jsx_content | indent(8, true) }}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '{{ background_color | default("#ffffff") }}',
  },
  content: {
    flexGrow: 1,
  },
});
{% endraw %}
```

---

## CODE GENERATOR

### code_generator.py

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from ..mapper.models import NativeElement, MappingResult

class CodeGenerator:
    def __init__(self):
        templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(templates_dir))
    
    def generate_component(self, name: str, element: NativeElement, props: list = None) -> str:
        """Génère un composant TSX."""
        template = self.env.get_template("component.tsx.j2")
        
        # Collecter les imports
        imports = self._collect_imports(element)
        
        # Générer le JSX
        jsx_tree = self._generate_jsx(element)
        
        return template.render(
            name=name,
            imports=list(imports),
            extra_imports=[],
            props=props or [],
            jsx_tree=jsx_tree
        )
    
    def generate_screen(self, name: str, components: list, content: NativeElement) -> str:
        """Génère un écran/page."""
        template = self.env.get_template("screen.tsx.j2")
        
        jsx_content = self._generate_jsx(content)
        
        return template.render(
            name=name,
            components=components,
            jsx_content=jsx_content,
            background_color="#ffffff"
        )
    
    def _collect_imports(self, element: NativeElement, imports: set = None) -> set:
        """Collecte tous les imports nécessaires."""
        if imports is None:
            imports = set()
        
        imports.add(element.component.value)
        
        for child in element.children:
            self._collect_imports(child, imports)
        
        return imports
    
    def _generate_jsx(self, element: NativeElement, indent: int = 0) -> str:
        """Génère le JSX pour un élément."""
        spaces = "  " * indent
        component = element.component.value
        
        # Props
        props_str = self._generate_props(element)
        style_str = self._generate_style_prop(element)
        
        all_props = " ".join(filter(None, [props_str, style_str]))
        
        # Si c'est du texte
        if element.text_content and not element.children:
            if component == "Text":
                return f"{spaces}<Text{' ' + all_props if all_props else ''}>{element.text_content}</Text>"
        
        # Si pas d'enfants
        if not element.children and not element.text_content:
            return f"{spaces}<{component}{' ' + all_props if all_props else ''} />"
        
        # Avec enfants
        lines = [f"{spaces}<{component}{' ' + all_props if all_props else ''}>"]
        
        if element.text_content:
            lines.append(f"{spaces}  <Text>{element.text_content}</Text>")
        
        for child in element.children:
            lines.append(self._generate_jsx(child, indent + 1))
        
        lines.append(f"{spaces}</{component}>")
        
        return "\n".join(lines)
    
    def _generate_props(self, element: NativeElement) -> str:
        """Génère les props en string."""
        props = []
        
        for key, value in element.props.items():
            if isinstance(value, bool):
                if value:
                    props.append(key)
            elif isinstance(value, str):
                props.append(f'{key}="{value}"')
            elif isinstance(value, dict):
                props.append(f'{key}={{{{ {self._dict_to_js(value)} }}}}')
            else:
                props.append(f'{key}={{{value}}}')
        
        return " ".join(props)
    
    def _generate_style_prop(self, element: NativeElement) -> str:
        """Génère la prop style."""
        if not element.style.properties:
            return ""
        
        style_obj = self._dict_to_js(element.style.properties)
        return f"style={{{{ {style_obj} }}}}"
    
    def _dict_to_js(self, d: dict) -> str:
        """Convertit un dict Python en objet JS."""
        parts = []
        for key, value in d.items():
            if isinstance(value, str):
                parts.append(f"{key}: '{value}'")
            elif isinstance(value, dict):
                parts.append(f"{key}: {{ {self._dict_to_js(value)} }}")
            else:
                parts.append(f"{key}: {value}")
        return ", ".join(parts)
```

---

## PROJECT GENERATOR

### project_generator.py

```python
from pathlib import Path
import json
from ..analyzer.models import AnalyzedSite, Screen

class ProjectGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
    
    def generate_project(self, analyzed: AnalyzedSite, code_gen):
        """Génère la structure complète du projet Expo."""
        
        # Créer la structure
        self._create_directories()
        
        # Générer package.json
        self._generate_package_json(analyzed)
        
        # Générer le theme
        self._generate_theme(analyzed.design_system)
        
        # Générer les écrans
        for screen in analyzed.screens:
            self._generate_screen(screen, code_gen)
        
        # Générer les composants
        for component in analyzed.components:
            self._generate_component(component, code_gen)
        
        # Générer la navigation
        self._generate_navigation(analyzed.navigation, analyzed.screens)
        
        # Générer app.json
        self._generate_app_json(analyzed)
    
    def _create_directories(self):
        """Crée l'arborescence de dossiers."""
        dirs = [
            "app/(tabs)",
            "app/(auth)",
            "components/ui",
            "components/shared",
            "hooks",
            "lib",
            "styles",
            "assets/images",
        ]
        for d in dirs:
            (self.output_dir / d).mkdir(parents=True, exist_ok=True)
    
    def _generate_package_json(self, analyzed: AnalyzedSite):
        """Génère package.json."""
        package = {
            "name": self._slugify(analyzed.source_url),
            "version": "1.0.0",
            "main": "expo-router/entry",
            "scripts": {
                "start": "expo start",
                "android": "expo start --android",
                "ios": "expo start --ios",
                "web": "expo start --web"
            },
            "dependencies": {
                "expo": "~50.0.0",
                "expo-router": "~3.4.0",
                "expo-status-bar": "~1.11.0",
                "react": "18.2.0",
                "react-native": "0.73.0",
                "react-native-safe-area-context": "4.8.2",
                "react-native-screens": "~3.29.0",
                "react-native-reanimated": "~3.6.0",
                "@react-native-async-storage/async-storage": "1.21.0"
            },
            "devDependencies": {
                "@types/react": "~18.2.0",
                "typescript": "^5.1.0"
            }
        }
        
        with open(self.output_dir / "package.json", "w") as f:
            json.dump(package, f, indent=2)
    
    def _generate_navigation(self, nav, screens: list[Screen]):
        """Génère la configuration de navigation Expo Router."""
        
        # _layout.tsx principal
        layout_content = '''
import { Stack } from 'expo-router';
import { ThemeProvider } from '@/lib/theme';

export default function RootLayout() {
  return (
    <ThemeProvider>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      </Stack>
    </ThemeProvider>
  );
}
'''
        with open(self.output_dir / "app/_layout.tsx", "w") as f:
            f.write(layout_content)
        
        # Tabs layout si nécessaire
        if nav.type == "bottom-tabs":
            self._generate_tabs_layout(screens)
    
    def _generate_tabs_layout(self, screens: list[Screen]):
        """Génère le layout avec tabs."""
        tabs = [s for s in screens if s.type.value in ["home", "dashboard", "profile", "settings"]]
        
        content = f'''
import {{ Tabs }} from 'expo-router';
import {{ Home, User, Settings }} from 'lucide-react-native';

export default function TabsLayout() {{
  return (
    <Tabs>
{''.join(self._generate_tab_screen(s) for s in tabs[:5])}
    </Tabs>
  );
}}
'''
        with open(self.output_dir / "app/(tabs)/_layout.tsx", "w") as f:
            f.write(content)
    
    def _generate_tab_screen(self, screen: Screen) -> str:
        icon = {"home": "Home", "profile": "User", "settings": "Settings"}.get(screen.type.value, "Home")
        return f'''
      <Tabs.Screen
        name="{screen.path.strip('/')}"
        options={{{{
          title: "{screen.name}",
          tabBarIcon: ({{ color }}) => <{icon} color={{color}} size={{24}} />,
        }}}}
      />
'''
    
    def _slugify(self, url: str) -> str:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace(".", "-").replace("www-", "")
    
    # ... autres méthodes
```

---

## SERVICE

### service.py

```python
from pathlib import Path
from ..analyzer.models import AnalyzedSite
from ..mapper.models import MappingResult
from .code_generator import CodeGenerator
from .project_generator import ProjectGenerator

class GeneratorService:
    def __init__(self, output_base: str = "./generated"):
        self.output_base = Path(output_base)
        self.code_gen = CodeGenerator()
    
    def generate(self, analyzed: AnalyzedSite, mappings: dict[str, MappingResult]) -> Path:
        """Génère le projet Expo complet."""
        
        # Créer le dossier de sortie
        project_name = self._get_project_name(analyzed.source_url)
        output_dir = self.output_base / project_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Générer le projet
        project_gen = ProjectGenerator(str(output_dir))
        project_gen.generate_project(analyzed, self.code_gen)
        
        return output_dir
    
    def _get_project_name(self, url: str) -> str:
        from urllib.parse import urlparse
        from datetime import datetime
        domain = urlparse(url).netloc.replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return f"{domain}_{timestamp}"
```

---

## LIVRABLES

```
backend/app/generator/
├── __init__.py
├── models.py
├── code_generator.py
├── style_generator.py
├── project_generator.py
├── templates/
│   ├── component.tsx.j2
│   ├── screen.tsx.j2
│   ├── stylesheet.ts.j2
│   └── package.json.j2
└── service.py
```

## CRITÈRES DE VALIDATION

- [ ] Génère des composants TSX valides
- [ ] Génère des StyleSheets corrects
- [ ] Crée la structure Expo Router
- [ ] package.json avec toutes les dépendances
- [ ] Projet buildable avec `npx expo start`

## TEMPS ESTIMÉ
5 heures
