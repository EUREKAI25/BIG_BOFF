from agency_objects import MRG, MRGContext, Method

def test_mrg_walks_elementlist_and_collects_results():
    what = {
        "name": "Root",
        "elementlist": [
            {"name": "ChildA", "elementlist": []},
            {"name": "ChildB", "elementlist": [{"name": "GrandChild", "elementlist": []}]},
        ],
    }

    seen = []

    def exec_hook(node, ctx):
        seen.append(node.get("name"))
        return True, {"ok": True}

    how = Method(name="noop", hook_execute=exec_hook)
    ok, payload = MRG().apply(what=what, how=how, ctx=MRGContext(run_id="t"))
    assert ok is True
    assert seen == ["Root", "ChildA", "ChildB", "GrandChild"]
    assert len(payload["results"]) == 4
