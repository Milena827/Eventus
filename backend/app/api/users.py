from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import hashlib
from typing import Optional
from app.database import get_db
from app.schemas import TestResultCreate, InterestCreate

router = APIRouter()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/")
def create_user(
    email: str,
    full_name: str,
    course: int,
    faculty: str,
    password: str = None,
    db: Session = Depends(get_db)
):
    """Создание нового пользователя"""
    existing = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": email}
    ).fetchone()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    
    pwd_hash = hash_password(password) if password else hash_password("default")
    
    result = db.execute(text("""
        INSERT INTO users (email, password_hash, full_name, course, faculty)
        VALUES (:email, :pwd, :full_name, :course, :faculty)
        RETURNING id
    """), {
        "email": email,
        "pwd": pwd_hash,
        "full_name": full_name,
        "course": course,
        "faculty": faculty
    })
    
    db.commit()
    user_id = result.fetchone()[0]
    
    return {"id": user_id, "message": "Пользователь создан"}

@router.put("/{user_id}")
def update_user(
    user_id: int,
    full_name: Optional[str] = None,
    course: Optional[int] = None,
    faculty: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Обновление данных пользователя"""
    
    user = db.execute(
        text("SELECT id FROM users WHERE id = :uid"),
        {"uid": user_id}
    ).fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    updates = []
    params = {"uid": user_id}
    
    if full_name:
        updates.append("full_name = :full_name")
        params["full_name"] = full_name
    if course:
        updates.append("course = :course")
        params["course"] = course
    if faculty:
        updates.append("faculty = :faculty")
        params["faculty"] = faculty
    
    if updates:
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = :uid"
        db.execute(text(query), params)
        db.commit()
        return {"message": "Пользователь обновлен"}
    
    return {"message": "Нет данных для обновления"}

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Удаление пользователя"""
    
    user = db.execute(
        text("SELECT id FROM users WHERE id = :uid"),
        {"uid": user_id}
    ).fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    db.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
    db.commit()
    
    return {"message": "Пользователь удален"}

@router.post("/{user_id}/test-results")
def add_test_results(
    user_id: int,
    results: list[TestResultCreate],
    db: Session = Depends(get_db)
):
    """Добавление результатов тестирования"""
    
    user = db.execute(
        text("SELECT id FROM users WHERE id = :uid"),
        {"uid": user_id}
    ).fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    for r in results:
        db.execute(text("""
            INSERT INTO test_results (user_id, competence_id, score, assessment_date)
            VALUES (:uid, :cid, :score, CURRENT_DATE)
            ON CONFLICT (user_id, competence_id) 
            DO UPDATE SET score = EXCLUDED.score, assessment_date = CURRENT_DATE
        """), {"uid": user_id, "cid": r.competence_id, "score": r.score})
    
    db.commit()
    return {"message": f"Сохранено {len(results)} результатов"}

@router.put("/{user_id}/test-results/{competence_id}")
def update_test_result(
    user_id: int,
    competence_id: int,
    score: int = Query(..., ge=200, le=800),
    db: Session = Depends(get_db)
):
    """Обновление результата тестирования"""
    
    result = db.execute(text("""
        SELECT id FROM test_results 
        WHERE user_id = :uid AND competence_id = :cid
    """), {"uid": user_id, "cid": competence_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Результат не найден")
    
    db.execute(text("""
        UPDATE test_results 
        SET score = :score, assessment_date = CURRENT_DATE
        WHERE user_id = :uid AND competence_id = :cid
    """), {"uid": user_id, "cid": competence_id, "score": score})
    
    db.commit()
    return {"message": "Результат обновлен"}

@router.delete("/{user_id}/test-results/{competence_id}")
def delete_test_result(
    user_id: int,
    competence_id: int,
    db: Session = Depends(get_db)
):
    """Удаление результата тестирования"""
    
    db.execute(text("""
        DELETE FROM test_results 
        WHERE user_id = :uid AND competence_id = :cid
    """), {"uid": user_id, "cid": competence_id})
    
    db.commit()
    return {"message": "Результат удален"}

@router.post("/{user_id}/interests")
def add_interests(
    user_id: int,
    interests: list[InterestCreate],
    db: Session = Depends(get_db)
):
    """Добавление интересов"""
    
    user = db.execute(
        text("SELECT id FROM users WHERE id = :uid"),
        {"uid": user_id}
    ).fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    for i in interests:
        db.execute(text("""
            INSERT INTO interests (user_id, category_id)
            VALUES (:uid, :cid)
            ON CONFLICT (user_id, category_id) DO NOTHING
        """), {"uid": user_id, "cid": i.category_id})
    
    db.commit()
    return {"message": f"Сохранено {len(interests)} интересов"}

@router.delete("/{user_id}/interests/{category_id}")
def delete_interest(
    user_id: int,
    category_id: int,
    db: Session = Depends(get_db)
):
    """Удаление интереса"""
    
    db.execute(text("""
        DELETE FROM interests 
        WHERE user_id = :uid AND category_id = :cid
    """), {"uid": user_id, "cid": category_id})
    
    db.commit()
    return {"message": "Интерес удален"}

@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Получение информации о пользователе"""
    user = db.execute(text("""
        SELECT id, email, full_name, course, faculty, created_at
        FROM users WHERE id = :uid
    """), {"uid": user_id}).fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return {
        "id": user[0],
        "email": user[1],
        "full_name": user[2],
        "course": user[3],
        "faculty": user[4],
        "created_at": user[5].isoformat() if user[5] else None
    }

@router.get("/{user_id}/full-profile")
def get_full_profile(user_id: int, db: Session = Depends(get_db)):
    """Получить полный профиль пользователя"""
    
    user = db.execute(text("""
        SELECT id, email, full_name, course, faculty
        FROM users WHERE id = :uid
    """), {"uid": user_id}).fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    results = db.execute(text("""
        SELECT c.id, c.name, c.description, tr.score
        FROM test_results tr
        JOIN competences c ON tr.competence_id = c.id
        WHERE tr.user_id = :uid
        ORDER BY tr.score ASC
    """), {"uid": user_id}).fetchall()
    
    interests = db.execute(text("""
        SELECT cat.id, cat.name
        FROM interests i
        JOIN categories cat ON i.category_id = cat.id
        WHERE i.user_id = :uid
    """), {"uid": user_id}).fetchall()
    
    return {
        "user": {
            "id": user[0],
            "email": user[1],
            "full_name": user[2],
            "course": user[3],
            "faculty": user[4]
        },
        "test_results": [
            {
                "competence_id": r[0],
                "competence_name": r[1],
                "description": r[2],
                "score": r[3]
            }
            for r in results
        ],
        "interests": [
            {
                "category_id": i[0],
                "category_name": i[1]
            }
            for i in interests
        ]
    }