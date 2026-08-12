from app.services.base_service import BaseService


class KnowledgeBaseService(BaseService):
    resource_name = "KnowledgeBase"

    async def create(self, payload):
        if isinstance(payload, dict):
            return await self.repository.create(payload)
        return await super().create(payload)
