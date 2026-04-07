def SuperValidate(context, catalog):
    context["validate_result"] = {
        "status": "success",
        "object_ident": context.get("object_ident")
    }
    return context
