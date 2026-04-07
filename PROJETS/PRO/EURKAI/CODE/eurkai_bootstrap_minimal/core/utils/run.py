"""Agnostic execution runner."""


def run(what: dict, how, catalog: dict) -> dict:
    return how(obj=what, catalog=catalog)
