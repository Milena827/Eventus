from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.database import get_db
from app.services.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    course: int
    faculty: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    course: int
    faculty: str


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    
    try:
        existing = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": request.email}
        ).fetchone()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        
        password_hash = get_password_hash(request.password)
        
        result = db.execute(text("""
            INSERT INTO users (email, password_hash, full_name, course, faculty)
            VALUES (:email, :pwd, :name, :course, :faculty)
            RETURNING id
        """), {
            "email": request.email,
            "pwd": password_hash,
            "name": request.full_name,
            "course": request.course,
            "faculty": request.faculty
        })
        
        db.commit()
        user_id = result.fetchone()[0]
        
        access_token = create_access_token(data={"sub": str(user_id)})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id,
            email=request.email,
            full_name=request.full_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Вход в систему"""
    
    user = db.execute(text("""
        SELECT id, email, full_name, password_hash
        FROM users
        WHERE email = :email
    """), {"email": form_data.username}).fetchone()
    
    if not user or not verify_password(form_data.password, user[3]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    access_token = create_access_token(data={"sub": str(user[0])})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user[0],
        email=user[1],
        full_name=user[2]
    )


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение данных текущего пользователя"""
    
    user = db.execute(text("""
        SELECT id, email, full_name, course, faculty
        FROM users WHERE id = :uid
    """), {"uid": current_user["id"]}).fetchone()
    
    return {
        "id": user[0],
        "email": user[1],
        "full_name": user[2],
        "course": user[3],
        "faculty": user[4]
    }