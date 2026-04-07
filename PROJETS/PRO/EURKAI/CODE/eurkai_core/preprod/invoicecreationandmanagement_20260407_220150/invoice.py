from typing import Any, Dict


class Invoice:
    """
    Data model — table invoices.
    """

    def __init__(self, id=None, user_id=None, amount=None, status=None, due_date=None, created_at=None):
        self.id = id
        self.user_id = user_id
        self.amount = amount
        self.status = status
        self.due_date = due_date
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
