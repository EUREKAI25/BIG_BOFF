from dataclasses import dataclass
from typing import Optional
from core.Object import Object
from core.project_types import ProjectType

@dataclass
class BaseProject(Object):
    description: str
    project_type: Optional[ProjectType] = None
