import json

def prompt_define(schema_path="template_schema.json", data_path="datas.json"):
    with open(schema_path) as f:
        schema = json.load(f)
    with open(data_path) as f:
        data = json.load(f)
    
    return schema["template"].format(**data)

if __name__ == "__main__":
    print(prompt_define())
