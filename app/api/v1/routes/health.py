from fastapi import APIRouter , Response , Depends , status,Request

from app.core.config import get_settings
from app.core.rate_limiter import limiter
from app.core.redis import get_redis_manager,get_otp_manager,get_cache_manager
from app.schemas import HealthResponse

router = APIRouter(prefix="/health",tags=["health"])
settings = get_settings()
redis = get_redis_manager()
#check for health 

@router.get("/live",status_code=status.HTTP_200_OK,response_model=HealthResponse)
@limiter.exempt
async def liveness_check(request:Request,response:Response)->HealthResponse:
    response.status_code = status.HTTP_200_OK
    return HealthResponse(api_service="Healthy",redis_service=redis.health["availability"],otp_service=redis.health["otp_db"],cache_service=redis.health["cache_db"])
