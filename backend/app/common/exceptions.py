from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
    ):
        self.code = code
        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "code": code,
                "message": message,
            },
        )


class NotFoundException(AppException):
    def __init__(self, resource: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} not found.",
        )