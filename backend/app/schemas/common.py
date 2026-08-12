from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    type: str | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    code: str
    message: str
    errors: list[ErrorDetail] | None = None
