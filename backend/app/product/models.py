from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_products():
    return []

@router.post("/")
async def create_product():
    return {"status": "created"}