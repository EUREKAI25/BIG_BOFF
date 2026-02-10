from dataclasses import dataclass
from typing import Optional, Dict, Any
from core.Object import Object

@dataclass
class ProjectType(Object):
    id: str
    category: str
    description: str
    objectif: str
    deadline: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None
    pipeline: Optional[Dict[str, Any]] = None
    mvp: Optional[Dict[str, Any]] = None
