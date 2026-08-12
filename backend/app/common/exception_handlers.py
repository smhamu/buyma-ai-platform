from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
            "errors": [
                {
                    "field": ".".join(
                        str(value)
                        for value in error["loc"]
                        if value != "body"
                    )
                    or None,
                    "message": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors()
            ],
        },
    )
