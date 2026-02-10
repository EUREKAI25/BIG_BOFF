from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ProjectType:
    id: str
    category: str
    description: str
    objectif: str
    deadline: Optional[str] = None

    schema: Optional[Dict[str, Any]] = None
    pipeline: Optional[Dict[str, Any]] = None
    mvp: Optional[Dict[str, Any]] = None
