from base_project import BaseProject
from project_types import ProjectType
from engine import run

types = [
    ProjectType(
        id="base_project",
        category="generic",
        description="base project",
        objectif="transform an intention into something observable",
    )
]

project = BaseProject(description="base project")

print(run(project, types))
