from fastapi import APIRouter

from app.api.v1.endpoints.universities import router as universities_router
from app.api.v1.chat import router as chat_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(universities_router)
api_v1_router.include_router(chat_router)