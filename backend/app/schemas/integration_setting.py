from pydantic import BaseModel, Field, field_validator


class RakutenTokenUpdate(BaseModel):
    token: str = Field(min_length=1, max_length=4096)

    @field_validator("token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        if value != value.strip() or any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError("The Rakuten token must not contain surrounding whitespace or control characters.")
        return value


class RakutenTokenSettingResponse(BaseModel):
    provider: str = "rakuten_product_search"
    configured: bool = False
