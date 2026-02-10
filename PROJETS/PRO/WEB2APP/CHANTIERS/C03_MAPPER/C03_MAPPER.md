 = self._map_element(element, all_imports, all_styles)
        
        return MappingResult(
            root=root,
            styles=all_styles,
            imports=all_imports,
            warnings=self.warnings,
            manual_review_needed=self.manual_review
        )
    
    def _map_element(self, element: ParsedElement, imports: set, styles: dict) -> NativeElement:
        """Mappe un élément individuel."""
        # Déterminer le composant natif
        component = get_native_component(
            element.tag,
            element.attributes,
            element.classes
        )
        
        # Ajouter l'import
        imports.add(component.value)
        
        # Mapper les props
        props = self._map_props(element, component)
        
        # Mapper les styles
        style = self._map_styles(element)
        
        # Créer l'élément natif
        native = NativeElement(
            component=component,
            props=props,
            style=style,
            text_content=element.text_content,
            source_tag=element.tag,
            source_classes=element.classes,
            imports=imports
        )
        
        # Mapper les enfants récursivement
        for child in element.children:
            native.children.append(self._map_element(child, imports, styles))
        
        return native
    
    def _map_props(self, element: ParsedElement, component: NativeComponentType) -> dict:
        """Mappe les attributs HTML en props RN."""
        props = {}
        
        for attr, value in element.attributes.items():
            mapped = PROP_MAPPING.get(attr)
            if mapped:
                props[mapped] = value
            elif attr.startswith("data-"):
                # Conserver les data attributes comme props custom
                props[attr] = value
        
        # Props spécifiques par composant
        if component == NativeComponentType.IMAGE:
            if "src" in element.attributes:
                props["source"] = {"uri": element.attributes["src"]}
        
        if component == NativeComponentType.TEXT_INPUT:
            if element.attributes.get("type") == "password":
                props["secureTextEntry"] = True
            if "placeholder" in element.attributes:
                props["placeholder"] = element.attributes["placeholder"]
        
        # Accessibilité
        if element.has_click_handler:
            props["accessible"] = True
            props["accessibilityRole"] = "button"
        
        return props
    
    def _map_styles(self, element: ParsedElement) -> NativeStyle:
        """Mappe les styles CSS en StyleSheet RN."""
        properties = {}
        
        # 1. Styles depuis les classes Tailwind
        if element.classes:
            tw_styles = parse_tailwind_classes(element.classes)
            properties.update(tw_styles)
        
        # 2. Styles computed (override)
        if element.styles:
            computed = self._map_computed_styles(element.styles)
            properties.update(computed)
        
        return NativeStyle(properties=properties)
    
    def _map_computed_styles(self, styles) -> dict:
        """Mappe les styles computed CSS."""
        props = {}
        
        if styles.display == "flex":
            props["flexDirection"] = styles.flex_direction or "row"
        
        if styles.justify_content:
            props["justifyContent"] = styles.justify_content
        
        if styles.align_items:
            props["alignItems"] = styles.align_items
        
        # ... autres mappings
        
        return props
```

---

## LIVRABLES

```
backend/app/mapper/
├── __init__.py
├── models.py
├── element_mapper.py
├── style_mapper.py
├── event_mapper.py
├── rules/
│   ├── elements.py
│   ├── tailwind.py
│   ├── colors.py
│   └── typography.py
└── service.py

tests/
└── test_mapper.py
```

## CRITÈRES DE VALIDATION

- [ ] Mappe tous les tags HTML courants
- [ ] Convertit les classes Tailwind en StyleSheet
- [ ] Gère les événements (onClick → onPress)
- [ ] Produit du code RN valide
- [ ] Tests passent

## TEMPS ESTIMÉ
4 heures
