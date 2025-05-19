from fastapi import FastAPI, BackgroundTasks, Depends
from app.core.config import settings
from app.services.detector import ViolenceDetector

# your auth router & security dependencies
from app.api.auth import router as auth_router
from app.api.auth import get_current_active_user, get_current_active_admin

# now import your two new routers
from app.api.users  import router as users_router
from app.api.alerts import router as alerts_router

app = FastAPI(title=settings.APP_NAME)

# 1) Auth endpoints (signup, login, reset…)
#    auth_router itself already has prefix="/auth" defined in auth.py,
#    so here we just include it without re-specifying the prefix:
app.include_router(
    auth_router,
    tags=["auth"],
)

# 2) User management — only Admins can call these
app.include_router(
    users_router,
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_active_admin)],
)

# 3) Alert endpoints — any logged-in user can call these
app.include_router(
    alerts_router,
    prefix="/alerts",
    tags=["alerts"],
    dependencies=[Depends(get_current_active_user)],
)

@app.get("/healthz", tags=["health"])
async def healthz():
    return {"status": "ok"}

@app.post("/start-detection", tags=["detection"])
async def start_detection(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_active_user),
):
    """
    Launches the violence detector in background. Must be logged in.
    """
    detector = ViolenceDetector(
        camera_index=settings.CAMERA_INDICES[0],
        seq_len=settings.SEQ_LEN,
        max_people=settings.MAX_PEOPLE,
        warning_th=settings.WARNING_THRESHOLD,
        urgent_th=settings.URGENT_THRESHOLD,
        smoothing_window=settings.SMOOTHING_WINDOW,
    )
    background_tasks.add_task(
        detector.run,
        settings.NORMAL_DIR,
        settings.VIOLENT_DIR,
        settings.MODEL_PATH,
    )
    return {"message": "Detection started"}
