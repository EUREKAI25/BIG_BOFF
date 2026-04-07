from typing import Any, Dict


class ApiClient:
    """
    API calls
    """

    def __init__(self):
        pass

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
