from storage.get_storage import get_storage

def on_success(context, catalog):
    hook = context.get("scenario", {}).get("hooks", {}).get("on_success")
    if not hook:
        return context
    fn = get_storage(catalog).get_function(hook)
    if fn:
        fn(context=context, catalog=catalog)
    return context
