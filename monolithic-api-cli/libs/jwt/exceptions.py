# libs/jwt/exceptions.py
class JwtVerificationError(Exception):
    """
    Structured verification error that won't crash the app state.
    code: stable string like JWT_ERR_EXPIRED, JWT_ERR_AUDIENCE, etc.
    detail: human-readable reason (safe for logs)
    """
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def as_dict(self) -> dict:
        return {"code": self.code, "detail": self.detail}
