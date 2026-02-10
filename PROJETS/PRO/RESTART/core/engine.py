from core.base_project import BaseProject
from core.project_types import ProjectType
from core.Agent import Agent

def run(project: BaseProject, types: list[ProjectType], agent: Agent):
    # options envoyées à choose : binaire "existe ?"
    options = [{"id": t.id, "description": t.description} for t in types]

    choice = agent.choose(
        options=options,
        context={"project_description": project.description},
    )

    result = choice.get("result", "NONE")

    if result in (None, "NONE"):
        return {"status": "TYPE_TO_CREATE", "type_id": "NONE"}

    pt = next((t for t in types if t.id == result), None)
    if not pt:
        return {"status": "TYPE_TO_CREATE", "type_id": result}

    project.project_type = pt
    return {"status": "OK", "project_type": pt.id}
