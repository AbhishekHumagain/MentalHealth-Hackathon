from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.internships import router as internships_router
from app.api.v1.endpoints.recommendations import router as recommendations_router
from app.api.v1.endpoints.student_profiles import router as student_profiles_router
from app.api.v1.endpoints.universities import router as universities_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(universities_router)
api_v1_router.include_router(student_profiles_router)
api_v1_router.include_router(internships_router)
api_v1_router.include_router(recommendations_router)
