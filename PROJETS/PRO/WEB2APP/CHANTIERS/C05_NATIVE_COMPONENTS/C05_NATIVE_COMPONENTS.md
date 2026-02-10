# CHANTIER 05 — NATIVE COMPONENTS (Bibliothèque React Native)

⚠️ **CE PROJET N'UTILISE PAS EUREKAI**

---

## OBJECTIF
Créer une bibliothèque de composants React Native de base que le générateur utilisera comme templates.

## PRÉREQUIS
Aucun (parallélisable)

## OUTPUTS
```
components/
├── ui/           # Button, Input, Card, Badge, Avatar...
├── layout/       # Container, Section, SafeArea...
├── navigation/   # TabBar, Header, BackButton...
└── shared/       # Loading, Error, Empty states...
```

---

## COMPOSANTS À CRÉER

### UI Components
```
Button.tsx        - Variantes: default, outline, ghost, destructive
Input.tsx         - Text input avec label, error
TextArea.tsx      - Multiline input
Card.tsx          - Container avec shadow
Badge.tsx         - Label coloré
Avatar.tsx        - Image circulaire + fallback
Checkbox.tsx      - Switch natif
Radio.tsx         - Radio buttons
Select.tsx        - Picker/Dropdown
Modal.tsx         - Overlay modal
Toast.tsx         - Notifications
Progress.tsx      - Barre de progression
Skeleton.tsx      - Loading placeholder
Divider.tsx       - Séparateur
```

### Layout Components
```
Container.tsx     - Max-width + padding
Section.tsx       - Espacement vertical
SafeArea.tsx      - Safe area wrapper
ScrollContainer.tsx - ScrollView configuré
KeyboardAvoiding.tsx - Keyboard aware
```

### Navigation Components
```
Header.tsx        - Header avec titre + actions
TabBar.tsx        - Bottom tabs custom
BackButton.tsx    - Bouton retour
```

### Shared Components
```
LoadingScreen.tsx - Full screen loader
ErrorScreen.tsx   - Affichage erreur
EmptyState.tsx    - État vide
```

---

## EXEMPLE : Button.tsx

```tsx
import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { theme } from '@/styles/theme';

type ButtonVariant = 'default' | 'outline' | 'ghost' | 'destructive';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  children: React.ReactNode;
  onPress?: () => void;
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export function Button({
  children,
  onPress,
  variant = 'default',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  style,
  textStyle,
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.7}
      style={[
        styles.base,
        styles[variant],
        styles[`size_${size}`],
        fullWidth && styles.fullWidth,
        isDisabled && styles.disabled,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator
          color={variant === 'default' ? '#fff' : theme.colors.primary}
          size="small"
        />
      ) : (
        <Text style={[styles.text, styles[`text_${variant}`], styles[`text_${size}`], textStyle]}>
          {children}
        </Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
  },
  
  // Variants
  default: {
    backgroundColor: theme.colors.primary,
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  destructive: {
    backgroundColor: theme.colors.error,
  },
  
  // Sizes
  size_sm: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  size_md: {
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  size_lg: {
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  
  fullWidth: {
    width: '100%',
  },
  disabled: {
    opacity: 0.5,
  },
  
  // Text
  text: {
    fontWeight: '600',
  },
  text_default: {
    color: '#ffffff',
  },
  text_outline: {
    color: theme.colors.text,
  },
  text_ghost: {
    color: theme.colors.primary,
  },
  text_destructive: {
    color: '#ffffff',
  },
  text_sm: {
    fontSize: 14,
  },
  text_md: {
    fontSize: 16,
  },
  text_lg: {
    fontSize: 18,
  },
});
```

---

## THEME

### styles/theme.ts

```typescript
export const theme = {
  colors: {
    primary: '#8b5cf6',
    primaryDark: '#7c3aed',
    secondary: '#64748b',
    background: '#ffffff',
    surface: '#f8fafc',
    text: '#0f172a',
    textMuted: '#64748b',
    border: '#e2e8f0',
    error: '#ef4444',
    success: '#22c55e',
    warning: '#f59e0b',
  },
  
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  
  radius: {
    sm: 4,
    md: 8,
    lg: 12,
    full: 9999,
  },
  
  typography: {
    h1: { fontSize: 32, fontWeight: '700' as const },
    h2: { fontSize: 24, fontWeight: '700' as const },
    h3: { fontSize: 20, fontWeight: '600' as const },
    body: { fontSize: 16, fontWeight: '400' as const },
    caption: { fontSize: 14, fontWeight: '400' as const },
  },
};

export type Theme = typeof theme;
```

---

## LIVRABLES

```
components/
├── ui/
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Card.tsx
│   ├── Badge.tsx
│   ├── Avatar.tsx
│   ├── Modal.tsx
│   ├── Toast.tsx
│   └── index.ts
├── layout/
│   ├── Container.tsx
│   ├── Section.tsx
│   └── index.ts
├── navigation/
│   ├── Header.tsx
│   ├── TabBar.tsx
│   └── index.ts
└── shared/
    ├── LoadingScreen.tsx
    ├── ErrorScreen.tsx
    └── index.ts

styles/
└── theme.ts
```

## CRITÈRES DE VALIDATION

- [ ] ~15 composants de base
- [ ] Thème configurable
- [ ] Props TypeScript typées
- [ ] Accessibilité de base
- [ ] Compatible iOS/Android

## TEMPS ESTIMÉ
6 heures
