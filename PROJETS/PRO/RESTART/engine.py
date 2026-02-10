from typing import List, Optional
from base_project import BaseProject
from project_types import ProjectType


def choose(project: BaseProject, types: List[ProjectType]) -> Optional[ProjectType]:
    for t in types:
        if t.description == project.description:
            return t
    return None


def validate(project_type: Optional[ProjectType]) -> bool:
    return project_type is not None


def apply(project: BaseProject, project_type: ProjectType) -> BaseProject:
    project.project_type = project_type
    return project


def run(project: BaseProject, types: List[ProjectType]):
    pt = choose(project, types)

    if not validate(pt):
        return {
            "status": "TYPE_TO_CREATE",
            "project_description": project.description,
        }

    project = apply(project, pt)

    return {
        "status": "OK",
        "project_type": project.project_type.id,
    }
