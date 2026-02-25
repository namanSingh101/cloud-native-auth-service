from fastapi import APIRouter , Response , Depends , status,Request
from app.core import limiter,get_settings
from app.schemas import HealthResponse

router = APIRouter(prefix="/health",tags=["health"])
settings = get_settings()

#check for health 

@router.get("/live",status_code=status.HTTP_200_OK,response_model=HealthResponse)
@limiter.exempt
async def liveness_check(request:Request,response:Response):
    response.status_code = status.HTTP_200_OK
    return {"status":"alive"}

# @router.get("/ready",status_code=status.HTTP_200_OK,response_model=HealthResponse)
# @limiter.exempt
# async def readiness_check(request:Request,response:Response):
#     response.status_code = status.HTTP_200_OK
#     return {"status":"ready"}