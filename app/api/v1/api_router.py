from fastapi import APIRouter

from app.api.v1.endpoints import agent, cms, finance, hr
from app.tools import cms_tools, hr_tools  # noqa: F401  registers tools at import time

api_router = APIRouter()

api_router.include_router(hr.router, prefix="/hr", tags=["HR"])
api_router.include_router(finance.router, prefix="/finance", tags=["Finance"])
api_router.include_router(cms.router, prefix="/cms", tags=["CMS"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent Router"])
