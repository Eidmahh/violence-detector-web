# app/main.py

import logging
from fastapi import FastAPI, BackgroundTasks, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from starlette.routing import Route

import cv2
import numpy as np
import tensorflow as tf

from app.core.config       import settings
from app.services.detector import ViolenceDetector

# ─────────── NEW: import your SQLAlchemy Base & engine ────────────────────────
from app.db.base    import Base
from app.db.session import engine

# Import routers & security dependencies
from app.api.auth   import router as auth_router, get_current_active_user, get_current_active_admin
from app.api.users  import router as users_router
from app.api.alerts import router as alerts_router

app = FastAPI(title=settings.APP_NAME)

# ─────────── NEW: ensure DB tables exist on startup ───────────────────────────
@app.on_event("startup")
def init_db():
    """
    Create all tables (users, alerts, etc.) before serving any requests.
    Safe to call on every startup.
    """
    Base.metadata.create_all(bind=engine)


# 1) Serve static assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2) Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# 3) Auth endpoints (mounted at /auth)
app.include_router(auth_router)

# 4) User management (Admin only)
app.include_router(
    users_router,
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_active_admin)],
)

# 5) Alert endpoints (Authenticated users)
app.include_router(
    alerts_router,
    prefix="/alerts",
    tags=["alerts"],
    dependencies=[Depends(get_current_active_user)],
)

# 6) MJPEG video stream (public)
@app.get("/video_feed", tags=["stream"])
def video_feed():
    def frame_generator():
        detector = ViolenceDetector(
            camera_index=settings.CAMERA_INDICES[0],
            seq_len=settings.SEQ_LEN,
            max_people=settings.MAX_PEOPLE,
            warning_th=settings.WARNING_THRESHOLD,
            urgent_th=settings.URGENT_THRESHOLD,
            smoothing_window=settings.SMOOTHING_WINDOW,
        )

        cap = cv2.VideoCapture(detector.cam, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS,          15)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 1) detect poses & extract features
            poses = detector.pose.detect(frame)
            feat  = detector.pose.keypoints_to_features(
                poses[:detector.max_people],
                frame.shape[:2]
            )
            detector.seq_buf.append(feat)

            # 2) infer & smooth once buffer is full
            label, color = "Gathering…", (0, 255, 255)
            if len(detector.seq_buf) == detector.seq_len:
                arr   = np.stack(detector.seq_buf, axis=0)[None, ...]
                score = float(detector._infer(tf.constant(arr))[0, 0].numpy())
                detector.pred_buf.append(score)
                avg   = float(np.mean(detector.pred_buf))
                if avg >= detector.urgent_th:
                    label, color = f"🚨 URGENT VIOLENCE ({avg:.2f})", (0, 0, 255)
                elif avg >= detector.warning_th:
                    label, color = f"⚠️ Warning ({avg:.2f})",   (0, 165, 255)
                else:
                    label, color = f"✔ Normal ({avg:.2f})",    (0, 255, 0)

            # 3) annotate frame
            out = frame.copy()
            cv2.putText(out, label, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

            # 4) yield as MJPEG chunk
            _, buffer = cv2.imencode(".jpg", out)
            frame_bytes = buffer.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                frame_bytes +
                b"\r\n"
            )

        cap.release()

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# 7) Root UI (Jinja2 template)
@app.get("/", tags=["ui"])
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 8) Health check
@app.get("/healthz", tags=["health"])
async def healthz():
    return {"status": "ok"}

# 9) Start background violence detection (auth required)
@app.post("/start-detection", tags=["detection"])
async def start_detection(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_active_user),
):
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

# 10) Log all mounted routes on startup
@app.on_event("startup")
def log_routes():
    logging.basicConfig(level=logging.INFO)
    for route in app.router.routes:
        if isinstance(route, Route):
            logging.info(
                f"Route: {route.name:30} → Path: {route.path!r} Methods: {route.methods}"
            )

# 11) Debug helper: dump routes as JSON
@app.get("/debug/routes", include_in_schema=False)
def debug_routes():
    return [
        {"path": route.path, "methods": list(route.methods), "name": route.name}
        for route in app.router.routes
        if isinstance(route, Route)
    ]