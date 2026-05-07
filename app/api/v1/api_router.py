from fastapi import APIRouter
from app.api.v1.endpoints import hr, finance, cms

api_router = APIRouter()

api_router.include_router(hr.router, prefix="/hr", tags=["HR"])
api_router.include_router(finance.router, prefix="/finance", tags=["Finance"])
api_router.include_router(cms.router, prefix="/cms", tags=["CMS"])