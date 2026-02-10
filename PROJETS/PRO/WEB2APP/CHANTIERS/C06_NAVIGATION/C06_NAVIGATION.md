# CHANTIER 06 — NAVIGATION (Expo Router)

⚠️ **CE PROJET N'UTILISE PAS EUREKAI**

---

## OBJECTIF
Analyser la structure de navigation du site web et générer la configuration Expo Router équivalente.

## PRÉREQUIS
- C02 Analyzer (AnalyzedSite avec screens et navigation)

## OUTPUTS
```
app/
├── _layout.tsx          # Root layout
├── (tabs)/
│   ├── _layout.tsx      # Tab navigator
│   ├── index.tsx        # Home
│   └── [autres tabs]
├── (auth)/
│   ├── _layout.tsx      # Auth stack
│   ├── login.tsx
│   └── register.tsx
└── [slug]/
    └── index.tsx        # Pages dynamiques
```

---

## TYPES DE NAVIGATION

### 1. Bottom Tabs
```
Quand : ≤5 écrans principaux, app type dashboard/social
```

### 2. Drawer
```
Quand : >5 écrans, navigation secondaire riche
```

### 3. Stack Only
```
Quand : Flow linéaire (onboarding, checkout)
```

### 4. Hybrid
```
Quand : Tabs + Stack pour détails
```

---

## SERVICE

### navigation_generator.py

```python
from pathlib import Path
from ..analyzer.models import AnalyzedSite, Screen, NavStructure

class NavigationGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.app_dir = output_dir / "app"
    
    def generate(self, analyzed: AnalyzedSite):
        """Génère toute la structure de navigation."""
        nav = analyzed.navigation
        screens = analyzed.screens
        
        # Root layout
        self._generate_root_layout(nav)
        
        # Navigation par type
        if nav.type == "bottom-tabs":
            self._generate_tabs_navigation(screens)
        elif nav.type == "drawer":
            self._generate_drawer_navigation(screens)
        else:
            self._generate_stack_navigation(screens)
        
        # Auth flow si présent
        if nav.has_auth_flow:
            self._generate_auth_flow(screens)
        
        # Pages dynamiques
        self._generate_dynamic_routes(screens)
    
    def _generate_root_layout(self, nav: NavStructure):
        """Génère app/_layout.tsx."""
        content = '''
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { ThemeProvider } from '@/lib/ThemeProvider';

export default function RootLayout() {
  return (
    <ThemeProvider>
      <StatusBar style="auto" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="[...slug]" />
      </Stack>
    </ThemeProvider>
  );
}
'''
        self._write_file("_layout.tsx", content)
    
    def _generate_tabs_navigation(self, screens: list[Screen]):
        """Génère la navigation par tabs."""
        (self.app_dir / "(tabs)").mkdir(exist_ok=True)
        
        # Sélectionner les écrans pour les tabs (max 5)
        tab_screens = [s for s in screens if s.type.value in 
                       ["home", "list", "dashboard", "profile", "settings"]][:5]
        
        # Générer le layout des tabs
        tabs_config = "\n".join([
            self._generate_tab_config(s, i) for i, s in enumerate(tab_screens)
        ])
        
        content = f'''
import {{ Tabs }} from 'expo-router';
import {{ Home, Search, User, Settings, Bell }} from 'lucide-react-native';
import {{ theme }} from '@/styles/theme';

const icons = {{ Home, Search, User, Settings, Bell }};

export default function TabsLayout() {{
  return (
    <Tabs
      screenOptions={{{{
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textMuted,
        headerShown: false,
      }}}}
    >
{tabs_config}
    </Tabs>
  );
}}
'''
        self._write_file("(tabs)/_layout.tsx", content)
        
        # Générer chaque page de tab
        for screen in tab_screens:
            self._generate_tab_screen(screen)
    
    def _generate_tab_config(self, screen: Screen, index: int) -> str:
        """Génère la config d'un tab."""
        icon = self._get_icon_for_screen(screen)
        name = "index" if index == 0 else screen.path.strip("/").replace("/", "-")
        
        return f'''
      <Tabs.Screen
        name="{name}"
        options={{{{
          title: "{screen.name}",
          tabBarIcon: ({{ color, size }}) => <{icon} color={{color}} size={{size}} />,
        }}}}
      />'''
    
    def _generate_tab_screen(self, screen: Screen):
        """Génère une page de tab."""
        name = "index" if screen.type.value == "home" else screen.path.strip("/")
        
        content = f'''
import {{ View, Text, StyleSheet }} from 'react-native';
import {{ SafeAreaView }} from 'react-native-safe-area-context';

export default function {screen.name.replace(" ", "")}Screen() {{
  return (
    <SafeAreaView style={{styles.container}}>
      <Text style={{styles.title}}>{screen.name}</Text>
      {{/* TODO: Contenu généré */}}
    </SafeAreaView>
  );
}}

const styles = StyleSheet.create({{
  container: {{
    flex: 1,
    backgroundColor: '#fff',
  }},
  title: {{
    fontSize: 24,
    fontWeight: '700',
    padding: 16,
  }},
}});
'''
        self._write_file(f"(tabs)/{name}.tsx", content)
    
    def _generate_auth_flow(self, screens: list[Screen]):
        """Génère le flow d'authentification."""
        (self.app_dir / "(auth)").mkdir(exist_ok=True)
        
        # Layout auth
        content = '''
import { Stack } from 'expo-router';

export default function AuthLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="login" />
      <Stack.Screen name="register" />
      <Stack.Screen name="forgot-password" />
    </Stack>
  );
}
'''
        self._write_file("(auth)/_layout.tsx", content)
        
        # Pages auth basiques
        for page in ["login", "register", "forgot-password"]:
            self._generate_auth_page(page)
    
    def _generate_auth_page(self, name: str):
        """Génère une page d'auth."""
        title = name.replace("-", " ").title()
        
        content = f'''
import {{ View, Text, StyleSheet }} from 'react-native';
import {{ SafeAreaView }} from 'react-native-safe-area-context';
import {{ Button }} from '@/components/ui/Button';
import {{ Input }} from '@/components/ui/Input';

export default function {name.replace("-", "").title()}Screen() {{
  return (
    <SafeAreaView style={{styles.container}}>
      <View style={{styles.content}}>
        <Text style={{styles.title}}>{title}</Text>
        <Input placeholder="Email" keyboardType="email-address" />
        {{'<Input placeholder="Password" secureTextEntry />' if name != 'forgot-password' else ''}}
        <Button fullWidth>{title}</Button>
      </View>
    </SafeAreaView>
  );
}}

const styles = StyleSheet.create({{
  container: {{ flex: 1, backgroundColor: '#fff' }},
  content: {{ flex: 1, padding: 24, justifyContent: 'center', gap: 16 }},
  title: {{ fontSize: 28, fontWeight: '700', marginBottom: 24, textAlign: 'center' }},
}});
'''
        self._write_file(f"(auth)/{name}.tsx", content)
    
    def _generate_dynamic_routes(self, screens: list[Screen]):
        """Génère les routes dynamiques."""
        dynamic_screens = [s for s in screens if s.params]
        
        for screen in dynamic_screens:
            # Ex: /product/:id → app/product/[id].tsx
            path_parts = screen.path.strip("/").split("/")
            
            # Créer le dossier si nécessaire
            if len(path_parts) > 1:
                folder = self.app_dir / path_parts[0]
                folder.mkdir(exist_ok=True)
    
    def _get_icon_for_screen(self, screen: Screen) -> str:
        """Détermine l'icône pour un écran."""
        mapping = {
            "home": "Home",
            "list": "Search",
            "dashboard": "Home",
            "profile": "User",
            "settings": "Settings",
        }
        return mapping.get(screen.type.value, "Home")
    
    def _write_file(self, path: str, content: str):
        """Écrit un fichier."""
        filepath = self.app_dir / path
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content.strip())
```

---

## LIVRABLES

```
backend/app/navigation/
├── __init__.py
├── models.py
├── navigation_analyzer.py
├── navigation_generator.py
└── service.py

# Output généré
app/
├── _layout.tsx
├── (tabs)/
├── (auth)/
└── [...slug]/
```

## CRITÈRES DE VALIDATION

- [ ] Génère root layout
- [ ] Génère tab navigation
- [ ] Génère auth flow
- [ ] Gère les routes dynamiques
- [ ] Navigation fonctionnelle

## TEMPS ESTIMÉ
3 heures
