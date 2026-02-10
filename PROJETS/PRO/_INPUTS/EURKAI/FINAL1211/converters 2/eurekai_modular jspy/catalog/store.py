#!/usr/bin/env python3
"""
EUREKAI Modular - Store (placeholder)
Gestion des vecteurs et données
"""

# Store en mémoire (à remplacer par DB)
_store = {}


def get(key: str):
    """Récupère une valeur du store"""
    return _store.get(key)


def set(key: str, value):
    """Stocke une valeur"""
    _store[key] = value


def delete(key: str):
    """Supprime une valeur"""
    if key in _store:
        del _store[key]


def keys():
    """Liste toutes les clés"""
    return list(_store.keys())


def clear():
    """Vide le store"""
    _store.clear()


def get_vector(vector_id: str) -> dict:
    """Récupère les paramètres d'un vecteur"""
    return get(f"vector:{vector_id}") or {}


def set_vector(vector_id: str, params: dict):
    """Stocke les paramètres d'un vecteur"""
    set(f"vector:{vector_id}", params)
