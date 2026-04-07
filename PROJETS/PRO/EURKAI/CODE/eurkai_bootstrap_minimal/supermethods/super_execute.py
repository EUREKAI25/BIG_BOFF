from core.utils.run import run

def SuperExecute(context, catalog):
    context["execute_result"] = run(context["what"], context["how"], catalog)
    return context
