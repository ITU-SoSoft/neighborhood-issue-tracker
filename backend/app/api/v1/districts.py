"""District management API routes."""

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import DatabaseSession
from app.models.district import District
from app.schemas.district import DistrictListResponse, DistrictResponse

router = APIRouter()


@router.get(
    "",
    response_model=DistrictListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_districts(
    db: DatabaseSession,
) -> DistrictListResponse:
    """List all districts.
    
    Public endpoint - no authentication required.
    """
    query = select(District).order_by(District.city, District.name)
    result = await db.execute(query)
    districts = result.scalars().all()

    return DistrictListResponse(
        items=[DistrictResponse.model_validate(d) for d in districts],
        total=len(districts),
    )

