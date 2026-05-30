from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import users, events, recommendations, auth

app = FastAPI(
    title="Eventus API",
    description="API для рекомендательной системы мероприятий",
    version="1.0.0"
)

# CORS — разрешаем всё для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])

@app.get("/")
def root():
    return {"message": "Eventus API работает", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}