import json
from utils import get_keys, get_value

def prompt_define(schema_path="template_schema.json", data_path="datas.json"):
    with open(schema_path) as f:
        keys = json.load(f)
    with open(data_path) as f:
        data = json.load(f)
    
    return "\n\n".join(f"# {k}\n{data[k]}" for k in keys)


def prompt_validate(promp_path) :
    template_keylist = get_keys(promp_path)
    for key, value in template_keylist:
        if 
        


if __name__ == "__main__":
    print(prompt_define())