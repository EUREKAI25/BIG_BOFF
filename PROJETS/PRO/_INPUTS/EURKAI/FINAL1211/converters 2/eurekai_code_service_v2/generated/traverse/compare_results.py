#!/usr/bin/env python3
"""
Compare les résultats JS natif vs Python API
"""
import json
import sys

def load_json(filepath):
    with open(filepath) as f:
        return json.load(f)

def compare_values(js_val, py_val, path=""):
    """Compare deux valeurs récursivement"""
    differences = []
    
    if type(js_val) != type(py_val):
        differences.append(f"{path}: types différents (JS: {type(js_val).__name__}, PY: {type(py_val).__name__})")
        return differences
    
    if isinstance(js_val, dict):
        all_keys = set(js_val.keys()) | set(py_val.keys())
        for key in all_keys:
            if key not in js_val:
                differences.append(f"{path}.{key}: manquant dans JS")
            elif key not in py_val:
                differences.append(f"{path}.{key}: manquant dans PY")
            else:
                differences.extend(compare_values(js_val[key], py_val[key], f"{path}.{key}"))
    
    elif isinstance(js_val, list):
        if len(js_val) != len(py_val):
            differences.append(f"{path}: longueurs différentes (JS: {len(js_val)}, PY: {len(py_val)})")
        else:
            for i, (jv, pv) in enumerate(zip(js_val, py_val)):
                differences.extend(compare_values(jv, pv, f"{path}[{i}]"))
    
    else:
        if js_val != py_val:
            differences.append(f"{path}: valeurs différentes (JS: {js_val}, PY: {py_val})")
    
    return differences

def main():
    print("=" * 60)
    print("COMPARAISON JS NATIF vs PYTHON API")
    print("=" * 60)
    print("")
    
    try:
        js_results = load_json('test_results_js.json')
        py_results = load_json('test_results_py.json')
    except FileNotFoundError as e:
        print(f"❌ Fichier manquant: {e}")
        print("\nExécutez d'abord:")
        print("  1. node test_native.js")
        print("  2. python3 test_api.py (avec le serveur qui tourne)")
        sys.exit(1)
    
    all_passed = True
    
    for test_name in js_results.keys():
        print(f"📋 {test_name}...")
        
        if test_name not in py_results:
            print(f"   ❌ Test manquant dans les résultats Python")
            all_passed = False
            continue
        
        diffs = compare_values(js_results[test_name], py_results[test_name], test_name)
        
        if diffs:
            print(f"   ❌ DIFFÉRENCES TROUVÉES:")
            for diff in diffs:
                print(f"      - {diff}")
            all_passed = False
        else:
            print(f"   ✅ IDENTIQUE")
    
    print("")
    print("=" * 60)
    if all_passed:
        print("🎉 TOUS LES TESTS PASSENT - JS et Python donnent les mêmes résultats!")
    else:
        print("⚠️  DES DIFFÉRENCES ONT ÉTÉ DÉTECTÉES")
    print("=" * 60)

if __name__ == '__main__':
    main()
