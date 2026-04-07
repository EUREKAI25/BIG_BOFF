def SuperRender(context, catalog):
    context["render_result"] = {
        "object_ident": context.get("object_ident")
    }
    return context
