def print_success(context, catalog):
    scenario = context.get("scenario")
    result = context.get("render_result")
    print(f"{scenario['ident']} ok sur {result['object_ident']}")
