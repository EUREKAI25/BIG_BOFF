from agency_objects import Method

def test_method_hook_order_and_data():
    events = []

    def before(node, ctx):
        events.append("before")
        return True, {"b": 1}

    def execute(node, ctx):
        events.append("execute")
        return True, {"x": 2}

    def after(node, ctx):
        events.append("after")
        return True, {"a": 3}

    m = Method(name="m", hook_before=before, hook_execute=execute, hook_after=after)

    ok_b, d_b = m.before({}, {})
    ok_x, d_x = m.execute({}, {})
    ok_a, d_a = m.after({}, {})

    assert (ok_b, ok_x, ok_a) == (True, True, True)
    assert events == ["before", "execute", "after"]
    assert d_b["b"] == 1 and d_x["x"] == 2 and d_a["a"] == 3
