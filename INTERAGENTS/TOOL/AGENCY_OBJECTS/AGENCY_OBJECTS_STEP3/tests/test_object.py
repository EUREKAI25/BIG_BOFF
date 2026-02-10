from agency_objects import Object

def test_object_has_elementlist():
    o = Object(name="Document")
    assert isinstance(o.elementlist, list)
    assert o.elementlist == []
