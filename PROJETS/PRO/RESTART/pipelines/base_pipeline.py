from core.System import System
from core.Agent import Agent
from core.base_project import BaseProject
from core.project_types import ProjectType
from core.engine import run

def execute_pipeline(project_description: str):
    system = System(base_dir=".")
    agent = Agent(system=system)

    types = [
        ProjectType(
            id="base_project",
            category="generic",
            description="base project",
            objectif="transform an intention into something observable",
            deadline=None,
            schema=None,
            pipeline=None,
            mvp=None,
        )
    ]

    project = BaseProject(description=project_description)
    return run(project, types, agent)

if __name__ == "__main__":
    print(execute_pipeline("base project"))
