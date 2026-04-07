from typing import Any, Dict


class User:
    """
    Data model — table users.
    """

    def __init__(self, id=None, email=None, password_hash=None, role=None, created_at=None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at

    def validate(self) -> Dict[str, Any]:
        errors = []
        return {"valid": len(errors) == 0, "errors": errors}

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def test(cls) -> bool:
        obj = cls()
        assert "valid" in obj.validate()
        return True
