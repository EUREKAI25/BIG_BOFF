"""Base Object class - EURKAI Core."""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class TestResult:
    """Result of object test."""
    def __init__(self, success: bool, message: str = ""):
        self.success = success
        self.message = message

    def __bool__(self):
        return self.success

    def __repr__(self):
        status = "✅" if self.success else "❌"
        return f"<TestResult {status} {self.message}>"


class Object(ABC):
    """
    Base EURKAI Object class.

    All objects in the system must inherit from this class and implement
    validate() and test() methods.

    Attributes:
        ident: Unique identifier (UUID)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        version: Object version
        parent: Optional parent object reference
        metadata: Flexible metadata dictionary
    """

    def __init__(
        self,
        ident: Optional[str] = None,
        created_at: Optional[datetime] = None,
        version: str = "1.0.0",
        parent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.ident = ident or str(uuid.uuid4())
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version = version
        self.parent = parent
        self.metadata = metadata or {}

    @abstractmethod
    def validate(self) -> bool:
        """
        Validate object coherence and constraints.

        Must be implemented by all subclasses.
        Returns True if object is valid, False otherwise.
        """
        pass

    @abstractmethod
    def test(self) -> TestResult:
        """
        Test object functionality.

        Must be implemented by all subclasses.
        Returns TestResult with success status and message.
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize object to dictionary."""
        return {
            "ident": self.ident,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "parent": self.parent,
            "metadata": self.metadata,
            "type": self.__class__.__name__,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Object":
        """
        Deserialize object from dictionary.

        Must be overridden by subclasses to handle specific attributes.
        """
        return cls(
            ident=data.get("ident"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            version=data.get("version", "1.0.0"),
            parent=data.get("parent"),
            metadata=data.get("metadata", {}),
        )

    def touch(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.ident[:8]}>"

    def __str__(self):
        return f"{self.__class__.__name__}({self.ident})"
