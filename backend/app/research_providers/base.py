from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class FetchedProduct:
    title: str
    brand: str | None
    price: Decimal
    currency: str
    availability: str
    external_product_id: str | None
    raw_payload: dict


class ResearchProvider(Protocol):
    async def fetch_product(self, url: str, supplier) -> FetchedProduct: ...
