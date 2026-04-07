from supermethods.super_get import SuperGet
from supermethods.super_execute import SuperExecute
from supermethods.super_validate import SuperValidate
from supermethods.super_render import SuperRender
from core.hooks.on_success import on_success

def mrg(context, catalog):
    context = SuperGet(context, catalog)
    context = SuperExecute(context, catalog)
    context = SuperValidate(context, catalog)
    context = SuperRender(context, catalog)
    context = on_success(context, catalog)
    return context
