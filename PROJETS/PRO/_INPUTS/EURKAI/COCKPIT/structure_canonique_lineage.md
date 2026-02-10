## 4.1. Structure canonique

La structure canonique combine :

- « : » pour la généalogie (parent → enfant)
- « . » pour l’accès interne (attributs et méthodes)

### Formes possibles :

```
<ParentObjectType>:<ChildObjectType>.<Attribute>
```

```
<ParentObjectType>:<ChildObjectType>.<Method>
```

```
<ParentObjectType>:<ChildObjectType>.<Method>()
```

```
<ParentObjectType>:<ChildObjectType>.<Method>(<params>)
```

### Déclinaisons sur plusieurs niveaux :

```
<A>:<B>:<C>.<Attribute>
```

```
<A>:<B>:<C>.<Method>()
```

```
<A>:<B>:<C>.<Method>(<params>)
```

### Déclinaisons internes supplémentaires :

```
<A>:<B>.bundle.<element>
```

```
<A>:<B>.structure.<field>.add()
```

```
<A>:<B>.methods.<X>(<params>)
```

```
<A>:<B>.attributes.<Y>
```
