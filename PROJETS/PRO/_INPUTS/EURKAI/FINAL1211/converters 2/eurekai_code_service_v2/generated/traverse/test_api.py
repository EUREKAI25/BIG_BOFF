#!/usr/bin/env python3
"""
Test Python via API - Compare avec les résultats JS natifs
"""
import json
from traverse_client import *

print("=== CHARGEMENT DES DONNÉES ===\n")

# Vider le store
Store.clear()

# Mêmes données que le test JS
Store.set('Object', {
    'name': 'Object',
    'attributeBundle': {
        'owned': [
            {'name': 'id', 'type': 'string'},
            {'name': 'createdAt', 'type': 'date'}
        ]
    }
})

Store.set('Object:Entity', {
    'name': 'Entity',
    'attributeBundle': {
        'owned': [
            {'name': 'label', 'type': 'string'},
            {'name': 'description', 'type': 'text'}
        ]
    }
})

Store.set('Object:Entity:Agent', {
    'name': 'Agent',
    'attributeBundle': {
        'owned': [
            {'name': 'status', 'type': 'enum'},
            {'name': 'capabilities', 'type': 'array'}
        ]
    }
})

Store.set('Object:Entity:Agent:AIAgent', {
    'name': 'AIAgent',
    'attributeBundle': {
        'owned': [
            {'name': 'model', 'type': 'string'},
            {'name': 'temperature', 'type': 'number'}
        ]
    }
})

Store.set('Object:Entity:Agent:HumanAgent', {
    'name': 'HumanAgent',
    'attributeBundle': {
        'owned': [
            {'name': 'email', 'type': 'string'},
            {'name': 'role', 'type': 'string'}
        ]
    }
})

print("Store keys:", Store.keys())
print("")

# === TESTS ===
print("=== TEST 1: get_ancestors ===")
ancestors = get_ancestors('Object:Entity:Agent:AIAgent')
print("get_ancestors('Object:Entity:Agent:AIAgent'):")
print(json.dumps(ancestors, indent=2))
print("")

print("=== TEST 2: get_descendants ===")
descendants = get_descendants('Object:Entity:Agent')
print("get_descendants('Object:Entity:Agent'):")
print(json.dumps(descendants, indent=2))
print("")

print("=== TEST 3: traverse_collect (direction: up) ===")
collect_up = traverse_collect('Object:Entity:Agent:AIAgent', {'direction': 'up'})
print("traverse_collect('Object:Entity:Agent:AIAgent', {direction: 'up'}):")
print(json.dumps(collect_up, indent=2))
print("")

print("=== TEST 4: traverse_collect (direction: down) ===")
collect_down = traverse_collect('Object:Entity:Agent:AIAgent', {'direction': 'down'})
print("traverse_collect('Object:Entity:Agent:AIAgent', {direction: 'down'}):")
print(json.dumps(collect_down, indent=2))
print("")

print("=== TEST 5: collect_inherited_elements ===")
inherited = collect_inherited_elements('Object:Entity:Agent:AIAgent', 'attributeBundle')
print("collect_inherited_elements('Object:Entity:Agent:AIAgent', 'attributeBundle'):")
print(json.dumps(inherited, indent=2))
print("")

print("=== TEST 6: traverse avec skipSelf ===")
skip_self = traverse_collect('Object:Entity:Agent', {'skipSelf': True})
print("traverse_collect('Object:Entity:Agent', {skipSelf: True}):")
print(json.dumps(skip_self, indent=2))
print("")

print("=== TEST 7: traverse sans includeRoot ===")
no_root = traverse_collect('Object:Entity:Agent', {'includeRoot': False})
print("traverse_collect('Object:Entity:Agent', {includeRoot: False}):")
print(json.dumps(no_root, indent=2))

# === EXPORT POUR COMPARAISON ===
results = {
    'test1_ancestors': ancestors,
    'test2_descendants': descendants,
    'test3_collect_up': collect_up,
    'test4_collect_down': collect_down,
    'test5_inherited': inherited,
    'test6_skipSelf': skip_self,
    'test7_noRoot': no_root
}

with open('test_results_py.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n✅ Résultats sauvegardés dans test_results_py.json")
