from typing import Any, Dict


class Payment:
    """
    Data model — table payments.
    """

    def __init__(self, id=None, invoice_id=None, amount=None, provider=None, transaction_id=None, paid_at=None):
        self.id = id
        self.invoice_id = invoice_id
        self.amount = amount
        self.provider = provider
        self.transaction_id = transaction_id
        self.paid_at = paid_at

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
