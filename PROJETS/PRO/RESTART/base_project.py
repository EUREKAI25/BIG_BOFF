from dataclasses import dataclass
from typing import Optional
from project_types import ProjectType


@dataclass
class BaseProject:
    description: str
    project_type: Optional[ProjectType] = None
