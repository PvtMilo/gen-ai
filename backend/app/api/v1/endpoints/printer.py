from fastapi import APIRouter

router = APIRouter(tags=["printer"])

@router.get("/printer")
def health():
    return {"ok": True}