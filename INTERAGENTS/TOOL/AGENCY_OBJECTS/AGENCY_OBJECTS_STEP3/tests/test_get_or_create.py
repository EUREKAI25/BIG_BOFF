from agency_objects import MRG, MRGContext, Method, PermissionGate, GetOrCreateScenario

def test_get_or_create_creates_on_missing_when_allowed():
    what = {"name": "Doc", "missing": True, "elementlist": []}

    def get_exec(node, ctx):
        if node.get("missing") is True:
            return False, {"missing": True}
        return True, {"found": True}

    def create_exec(node, ctx):
        node["created"] = True
        node.pop("missing", None)
        return True, {"created": True}

    get_m = Method(name="get", hook_execute=get_exec)
    create_m = Method(name="create", permission=PermissionGate(allowed=True), hook_execute=create_exec)

    how = GetOrCreateScenario(name="getOrCreate", get_method=get_m, create_method=create_m)
    ok, _payload = MRG().apply(what=what, how=how, ctx=MRGContext(run_id="t"))

    assert ok is True
    assert what.get("created") is True
    assert what.get("missing") is None

def test_get_or_create_fails_when_create_forbidden():
    what = {"name": "Doc", "missing": True, "elementlist": []}

    def get_exec(node, ctx):
        return False, {"missing": True}

    def create_exec(node, ctx):
        node["created"] = True
        return True, {"created": True}

    get_m = Method(name="get", hook_execute=get_exec)
    create_m = Method(name="create", permission=PermissionGate(allowed=False, reason="nope"), hook_execute=create_exec)

    how = GetOrCreateScenario(name="getOrCreate", get_method=get_m, create_method=create_m)
    ok, _payload = MRG().apply(what=what, how=how, ctx=MRGContext(run_id="t"))

    assert ok is False
    assert what.get("created") is None
