from fastapi import HTTPException


class ACCAIException(HTTPException):
    """Base exception for ACCAI application errors."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
    ):
        self.code = code
        self.message = message

        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "error": {
                    "code": code,
                    "message": message,
                },
            },
        )