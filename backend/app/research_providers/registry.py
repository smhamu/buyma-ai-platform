from functools import lru_cache

from app.common.exceptions import AppException
from app.research_providers.json_ld import SchemaOrgProductProvider


class ResearchProviderRegistry:
    def __init__(self, providers=None):
        self.providers = providers or {"schema_org_product_v1": SchemaOrgProductProvider()}

    def get(self, parser_key: str | None):
        if not parser_key or parser_key not in self.providers:
            raise AppException(409, "RESEARCH_PROVIDER_NOT_CONFIGURED", "The supplier has no supported research provider.")
        return self.providers[parser_key]


@lru_cache
def get_research_provider_registry() -> ResearchProviderRegistry:
    return ResearchProviderRegistry()
