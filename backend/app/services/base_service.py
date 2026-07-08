from uuid import UUID

from app.common.exceptions import NotFoundException


class BaseService:
    resource_name = "Resource"

    def __init__(self, repository):
        self.repository = repository

    async def create(self, payload):
        return await self.repository.create(payload.model_dump())

    async def list(self):
        return await self.repository.find_all()

    async def get(self, obj_id: UUID):
        obj = await self.repository.find_by_id(obj_id)

        if obj is None:
            raise NotFoundException(self.resource_name)

        return obj

    async def update(self, obj_id: UUID, payload):
        obj = await self.get(obj_id)

        return await self.repository.update(
            obj,
            payload.model_dump(exclude_unset=True),
        )

    async def delete(self, obj_id: UUID):
        obj = await self.get(obj_id)
        await self.repository.delete(obj)

        return {"id": str(obj_id)}