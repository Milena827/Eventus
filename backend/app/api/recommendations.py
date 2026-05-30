from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.schemas import UserActionCreate

router = APIRouter()

# Пары смежных компетенций (ключ — слабая компетенция, значение — сильная компетенция-сосед)
ADJACENT_PAIRS = {
    'Лидерство': 'Планирование',
    'Планирование': 'Лидерство',
    'Коммуникативная грамотность': 'Эмоциональный интеллект',
    'Эмоциональный интеллект': 'Коммуникативная грамотность',
    'Анализ информации': 'Ориентация на результат',
    'Ориентация на результат': 'Анализ информации',
    'Партнерство/сотрудничество': 'Клиентоориентированность',
    'Клиентоориентированность': 'Партнерство/сотрудничество',
    'Саморазвитие': 'Стрессоустойчивость',
    'Стрессоустойчивость': 'Саморазвитие',
    'Следование правилам': 'Планирование',
}

ADJACENT_TEXTS = {
    ('Лидерство', 'Планирование'): 'План без лидерства не работает. Лидерство без плана — тоже.',
    ('Планирование', 'Лидерство'): 'Научились планировать — осваивайте управление людьми.',
    ('Коммуникативная грамотность', 'Эмоциональный интеллект'): 'Грамотная речь и понимание эмоций — две опоры эффективного общения.',
    ('Эмоциональный интеллект', 'Коммуникативная грамотность'): 'Развили эмпатию — займитесь подачей материала.',
    ('Анализ информации', 'Ориентация на результат'): 'Анализ ради анализа бесполезен. Превращайте данные в конкретные шаги.',
    ('Ориентация на результат', 'Анализ информации'): 'Быстро идёте к цели — проверьте маршрут с помощью анализа.',
    ('Партнерство/сотрудничество', 'Клиентоориентированность'): 'Командная работа и фокус на клиенте прямо влияют на бизнес-показатели.',
    ('Клиентоориентированность', 'Партнерство/сотрудничество'): 'Знаете потребности клиента — встройте это в командные процессы.',
    ('Саморазвитие', 'Стрессоустойчивость'): 'Новые навыки снижают тревожность и укрепляют устойчивость.',
    ('Стрессоустойчивость', 'Саморазвитие'): 'Сохраняете спокойствие — используйте этот ресурс для профессионального роста.',
    ('Следование правилам', 'Планирование'): 'Дисциплина плюс график — база для predictable results.',
}

@router.get("/{user_id}")
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    """Получение двух подборок рекомендаций"""
    
    user = db.execute(
        text("SELECT id FROM users WHERE id = :uid"), 
        {"uid": user_id}
    ).fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # ============================================
    # ПОДБОРКА 1: ПО КОМПЕТЕНЦИЯМ
    # ============================================
    
    # Получаем ВСЕ результаты тестирования
    all_results = db.execute(text("""
        SELECT tr.competence_id, tr.score, c.name as competence_name
        FROM test_results tr
        JOIN competences c ON tr.competence_id = c.id
        WHERE tr.user_id = :uid
        ORDER BY tr.score ASC
    """), {"uid": user_id}).fetchall()
    
    if not all_results:
        return {"competence_based": [], "interest_based": []}
    
    # Слабые (<400) и сильные (>600) компетенции
    weak_competences = [(r[0], r[1], r[2]) for r in all_results if r[1] < 400]
    strong_competences = [(r[0], r[1], r[2]) for r in all_results if r[1] > 600]
    
    competence_events = []
    seen_ids = set()
    
    # 1. Подбираем по слабым компетенциям
    for wc in weak_competences[:3]:
        events = db.execute(text("""
            SELECT DISTINCT e.id, e.title, e.description, e.event_date, 
                   e.location, e.format, e.image_url, ec.relevance, c.name as competence_name
            FROM events e
            JOIN event_competences ec ON e.id = ec.event_id
            JOIN competences c ON ec.competence_id = c.id
            WHERE ec.competence_id = :cid
              AND e.status = 'active'
              AND (e.event_date IS NULL OR e.event_date >= CURRENT_DATE)
            ORDER BY ec.relevance DESC, e.event_date ASC
            LIMIT 15
        """), {"cid": wc[0]}).fetchall()
        
        for e in events:
            if e[0] not in seen_ids:
                seen_ids.add(e[0])
                competence_events.append({
                    "id": e[0],
                    "title": e[1],
                    "description": e[2],
                    "event_date": e[3].isoformat() if e[3] else None,
                    "location": e[4],
                    "format": e[5],
                    "image_url": e[6],
                    "relevance": e[7],
                    "competence_score": wc[1],
                    "competence_name": e[8],
                    "recommendation_type": "weak_competence",
                    "adjacent_text": None
                })
    
    # 2. Эффект «соседнего развития»
    for wc in weak_competences:
        weak_name = wc[2]
        
        # Ищем смежную компетенцию
        if weak_name in ADJACENT_PAIRS:
            adjacent_name = ADJACENT_PAIRS[weak_name]
            
            # Проверяем, сильна ли смежная у пользователя
            adjacent_strong = next((s for s in strong_competences if s[2] == adjacent_name), None)
            
            if adjacent_strong:
                # Ищем мероприятия по СЛАБОЙ компетенции, но с текстом про СИЛЬНУЮ
                events = db.execute(text("""
                    SELECT DISTINCT e.id, e.title, e.description, e.event_date, 
                           e.location, e.format, e.image_url, ec.relevance, c.name as competence_name
                    FROM events e
                    JOIN event_competences ec ON e.id = ec.event_id
                    JOIN competences c ON ec.competence_id = c.id
                    WHERE ec.competence_id = :cid
                      AND e.status = 'active'
                      AND (e.event_date IS NULL OR e.event_date >= CURRENT_DATE)
                    ORDER BY ec.relevance DESC, e.event_date ASC
                    LIMIT 10
                """), {"cid": wc[0]}).fetchall()
                
                adjacent_text = ADJACENT_TEXTS.get(
                    (weak_name, adjacent_name),
                    f'Ваше сильное «{adjacent_name}» поможет развить «{weak_name}»!'
                )
                
                for e in events:
                    if e[0] not in seen_ids:
                        seen_ids.add(e[0])
                        competence_events.append({
                            "id": e[0],
                            "title": e[1],
                            "description": e[2],
                            "event_date": e[3].isoformat() if e[3] else None,
                            "location": e[4],
                            "format": e[5],
                            "image_url": e[6],
                            "relevance": e[7],
                            "competence_score": wc[1],
                            "competence_name": e[8],
                            "recommendation_type": "adjacent_development",
                            "adjacent_text": adjacent_text,
                            "adjacent_strong": adjacent_name
                        })
    
    # ============================================
    # ПОДБОРКА 2: ПО ИНТЕРЕСАМ
    # ============================================
    user_interests = db.execute(text("""
        SELECT i.category_id, cat.name as category_name
        FROM interests i
        JOIN categories cat ON i.category_id = cat.id
        WHERE i.user_id = :uid
    """), {"uid": user_id}).fetchall()
    
    interest_events = []
    seen_interest_ids = set()
    
    if user_interests:
        for interest in user_interests:
            events = db.execute(text("""
                SELECT DISTINCT e.id, e.title, e.description, e.event_date,
                       e.location, e.format, e.image_url
                FROM events e
                JOIN event_categories ec ON e.id = ec.event_id
                WHERE ec.category_id = :cid
                  AND e.status = 'active'
                  AND (e.event_date IS NULL OR e.event_date >= CURRENT_DATE)
                ORDER BY e.event_date ASC
                LIMIT 20
            """), {"cid": interest[0]}).fetchall()
            
            for e in events:
                if e[0] not in seen_interest_ids:
                    seen_interest_ids.add(e[0])
                    interest_events.append({
                        "id": e[0],
                        "title": e[1],
                        "description": e[2],
                        "event_date": e[3].isoformat() if e[3] else None,
                        "location": e[4],
                        "format": e[5],
                        "image_url": e[6],
                        "interest_weight": 1,
                        "interest_name": interest[1]
                    })
    
    return {
        "competence_based": competence_events[:40],
        "interest_based": interest_events[:30]
    }


@router.post("/{user_id}/actions")
def add_action(
    user_id: int,
    action: UserActionCreate,
    db: Session = Depends(get_db)
):
    """Запись действия пользователя"""
    
    action_type = db.execute(
        text("SELECT id FROM action_types WHERE name = :name"),
        {"name": action.action_type}
    ).fetchone()
    
    if not action_type:
        raise HTTPException(status_code=400, detail="Неизвестный тип действия")
    
    # Если это оценка (rate) — проверяем, не ставил ли уже пользователь оценку этому мероприятию
    if action.action_type == 'rate' and action.rating:
        existing = db.execute(text("""
            SELECT id FROM user_actions 
            WHERE user_id = :uid AND event_id = :eid 
            AND action_type_id = :aid AND rating IS NOT NULL
        """), {
            "uid": user_id,
            "eid": action.event_id,
            "aid": action_type[0]
        }).fetchone()
        
        if existing:
            # Обновляем существующую оценку
            db.execute(text("""
                UPDATE user_actions 
                SET rating = :rating, created_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """), {"rating": action.rating, "id": existing[0]})
            db.commit()
            return {"id": existing[0], "message": "Оценка обновлена"}
    
    # Если это отзыв (review_text) — тоже проверяем
    if action.action_type == 'rate' and action.review_text:
        existing = db.execute(text("""
            SELECT id FROM user_actions 
            WHERE user_id = :uid AND event_id = :eid 
            AND action_type_id = :aid AND review_text IS NOT NULL
        """), {
            "uid": user_id,
            "eid": action.event_id,
            "aid": action_type[0]
        }).fetchone()
        
        if existing:
            # Обновляем существующий отзыв
            db.execute(text("""
                UPDATE user_actions 
                SET review_text = :text, created_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """), {"text": action.review_text, "id": existing[0]})
            db.commit()
            return {"id": existing[0], "message": "Отзыв обновлен"}
    
    # Если ничего не найдено — создаем новую запись
    result = db.execute(text("""
        INSERT INTO user_actions (user_id, event_id, action_type_id, rating, review_text)
        VALUES (:uid, :eid, :aid, :rating, :review)
        RETURNING id
    """), {
        "uid": user_id,
        "eid": action.event_id,
        "aid": action_type[0],
        "rating": action.rating,
        "review": action.review_text
    })
    
    db.commit()
    action_id = result.fetchone()[0]
    
    return {"id": action_id, "message": f"Действие '{action.action_type}' сохранено"}

@router.get("/{user_id}/actions")
def get_user_actions(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Получение истории действий пользователя"""
    
    actions = db.execute(text("""
        SELECT ua.id, ua.event_id, e.title, at.name as action_type, 
               ua.rating, ua.review_text, ua.created_at
        FROM user_actions ua
        JOIN events e ON ua.event_id = e.id
        JOIN action_types at ON ua.action_type_id = at.id
        WHERE ua.user_id = :uid
        ORDER BY ua.created_at DESC
        LIMIT :limit
    """), {"uid": user_id, "limit": limit}).fetchall()
    
    return [
        {
            "id": a[0],
            "event_id": a[1],
            "event_title": a[2],
            "action_type": a[3],
            "rating": a[4],
            "review_text": a[5],
            "created_at": a[6].isoformat() if a[6] else None
        }
        for a in actions
    ]

@router.delete("/{user_id}/actions/{action_id}")
def delete_action(
    user_id: int,
    action_id: int,
    db: Session = Depends(get_db)
):
    """Удаление действия пользователя"""
    
    result = db.execute(text("""
        DELETE FROM user_actions 
        WHERE id = :aid AND user_id = :uid
        RETURNING id
    """), {"aid": action_id, "uid": user_id})
    
    deleted = result.fetchone()
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Действие не найдено")
    
    db.commit()
    return {"message": "Действие удалено"}