from pipelines.base_pipeline import execute_pipeline

def test_pipeline_ok():
    res = execute_pipeline("base project")
    assert res["status"] == "OK"
    assert res["project_type"] == "base_project"

def test_pipeline_type_to_create():
    res = execute_pipeline("something else")
    assert res["status"] == "TYPE_TO_CREATE"
