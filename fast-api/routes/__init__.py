from pathlib import Path
import sys
from fastapi import APIRouter

from .auth_routes import router as auth_router
from .app_routes import router as app_router
from .prompt_routes import router as prompt_router


router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(app_router, prefix="/app", tags=["app"])
router.include_router(prompt_router, prefix="/prompt", tags=["prompt"])
