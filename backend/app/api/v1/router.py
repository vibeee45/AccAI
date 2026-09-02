from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
def health():
    """
    Basic API health check.
    """

    return {
        "status": "ok",
        "service": "accai-backend",
        "version": "v1",
    }