import json

def get_keys(json_path):
    with open(json_path) as f:
        return list(json.load(f).keys())

def get_value(json_path, key):
    with open(json_path) as f:
        return json.load(f).get(key)