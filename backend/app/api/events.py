from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.schemas import EventCreate

router = APIRouter()

@router.get("/")
def get_events(
    limit: int = Query(50, ge=1, le=500),
    city: Optional[str] = None,
    format: Optional[str] = None,
    status: str = "active",
    db: Session = Depends(get_db)
):
    """Получение списка мероприятий с фильтрацией"""
    query = """
        SELECT id, title, description, event_date, location, 
               format, image_url, status
        FROM events 
        WHERE 1=1
    """
    params = {}
    
    if status:
        query += " AND status = :status"
        params["status"] = status
    
    if city:
        query += " AND location LIKE :city"
        params["city"] = f"%{city}%"
    
    if format:
        query += " AND format = :format"
        params["format"] = format
    
    query += " ORDER BY event_date ASC NULLS LAST LIMIT :limit"
    params["limit"] = limit
    
    events = db.execute(text(query), params).fetchall()
    
    return [
        {
            "id": e[0],
            "title": e[1],
            "description": e[2],
            "event_date": e[3].isoformat() if e[3] else None,
            "location": e[4],
            "format": e[5],
            "image_url": e[6],
            "status": e[7]
        }
        for e in events
    ]

@router.get("/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Получение детальной информации о мероприятии"""
    event = db.execute(text("""
        SELECT e.id, e.title, e.description, e.url, e.source_id, 
               e.event_date, e.location, e.format, e.image_url, e.status,
               s.name as source_name
        FROM events e
        LEFT JOIN sources s ON e.source_id = s.id
        WHERE e.id = :eid
    """), {"eid": event_id}).fetchone()
    
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    
    competences = db.execute(text("""
        SELECT c.id, c.name, ec.relevance
        FROM event_competences ec
        JOIN competences c ON ec.competence_id = c.id
        WHERE ec.event_id = :eid
    """), {"eid": event_id}).fetchall()
    
    categories = db.execute(text("""
        SELECT cat.id, cat.name
        FROM event_categories ec
        JOIN categories cat ON ec.category_id = cat.id
        WHERE ec.event_id = :eid
    """), {"eid": event_id}).fetchall()
    
    return {
        "id": event[0],
        "title": event[1],
        "description": event[2],
        "url": event[3],
        "source_id": event[4],
        "event_date": event[5].isoformat() if event[5] else None,
        "location": event[6],
        "format": event[7],
        "image_url": event[8],
        "status": event[9],
        "source_name": event[10] if len(event) > 10 else None,
        "competences": [{"id": c[0], "name": c[1], "relevance": c[2]} for c in competences],
        "categories": [{"id": cat[0], "name": cat[1]} for cat in categories]
    }

@router.post("/")
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db)
):
    """Ручное добавление мероприятия"""
    location = event.location or event.city
    if event.city and event.location and event.city not in event.location:
        location = f"{event.city}, {event.location}"
    
    result = db.execute(text("""
        INSERT INTO events (title, description, url, source_id, event_date, 
                          location, format, image_url, status)
        VALUES (:title, :desc, :url, :sid, :edate, :loc, :format, :img, 'active')
        RETURNING id
    """), {
        "title": event.title,
        "desc": event.description,
        "url": event.url,
        "sid": event.source_id,
        "edate": event.event_date,
        "loc": location,
        "format": event.format,
        "img": event.image_url
    })
    
    db.commit()
    event_id = result.fetchone()[0]
    
    return {"id": event_id, "message": "Мероприятие добавлено"}

@router.put("/{event_id}")
def update_event(
    event_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    event_date: Optional[datetime] = None,
    location: Optional[str] = None,
    format: Optional[str] = None,
    image_url: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Обновление мероприятия"""
    
    event = db.execute(
        text("SELECT id FROM events WHERE id = :eid"),
        {"eid": event_id}
    ).fetchone()
    
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    
    updates = []
    params = {"eid": event_id}
    
    if title is not None:
        updates.append("title = :title")
        params["title"] = title
    if description is not None:
        updates.append("description = :desc")
        params["desc"] = description
    if event_date is not None:
        updates.append("event_date = :edate")
        params["edate"] = event_date
    if location is not None:
        updates.append("location = :loc")
        params["loc"] = location
    if format is not None:
        updates.append("format = :format")
        params["format"] = format
    if image_url is not None:
        updates.append("image_url = :img")
        params["img"] = image_url
    if status is not None:
        updates.append("status = :status")
        params["status"] = status
    
    if updates:
        query = f"UPDATE events SET {', '.join(updates)} WHERE id = :eid"
        db.execute(text(query), params)
        db.commit()
        return {"message": "Мероприятие обновлено"}
    
    return {"message": "Нет данных для обновления"}

@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    hard_delete: bool = False,
    db: Session = Depends(get_db)
):
    """Удаление мероприятия (мягкое или полное)"""
    
    event = db.execute(
        text("SELECT id FROM events WHERE id = :eid"),
        {"eid": event_id}
    ).fetchone()
    
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    
    if hard_delete:
        db.execute(text("DELETE FROM events WHERE id = :eid"), {"eid": event_id})
        message = "Мероприятие полностью удалено"
    else:
        db.execute(
            text("UPDATE events SET status = 'deleted' WHERE id = :eid"),
            {"eid": event_id}
        )
        message = "Мероприятие помечено как удаленное"
    
    db.commit()
    return {"message": message}

@router.post("/{event_id}/competences")
def add_event_competence(
    event_id: int, 
    competence_id: int, 
    relevance: int = 3, 
    db: Session = Depends(get_db)
):
    """Привязка мероприятия к компетенции"""
    db.execute(text("""
        INSERT INTO event_competences (event_id, competence_id, relevance)
        VALUES (:eid, :cid, :rel)
        ON CONFLICT (event_id, competence_id) 
        DO UPDATE SET relevance = EXCLUDED.relevance
    """), {"eid": event_id, "cid": competence_id, "rel": relevance})
    
    db.commit()
    return {"message": "Компетенция привязана"}

@router.delete("/{event_id}/competences/{competence_id}")
def remove_event_competence(
    event_id: int,
    competence_id: int,
    db: Session = Depends(get_db)
):
    """Удаление привязки мероприятия к компетенции"""
    
    db.execute(text("""
        DELETE FROM event_competences 
        WHERE event_id = :eid AND competence_id = :cid
    """), {"eid": event_id, "cid": competence_id})
    
    db.commit()
    return {"message": "Привязка к компетенции удалена"}

@router.post("/{event_id}/categories")
def add_event_category(
    event_id: int, 
    category_id: int, 
    db: Session = Depends(get_db)
):
    """Привязка мероприятия к категории интереса"""
    db.execute(text("""
        INSERT INTO event_categories (event_id, category_id)
        VALUES (:eid, :cid)
        ON CONFLICT (event_id, category_id) DO NOTHING
    """), {"eid": event_id, "cid": category_id})
    
    db.commit()
    return {"message": "Категория привязана"}

@router.delete("/{event_id}/categories/{category_id}")
def remove_event_category(
    event_id: int,
    category_id: int,
    db: Session = Depends(get_db)
):
    """Удаление привязки мероприятия к категории"""
    
    db.execute(text("""
        DELETE FROM event_categories 
        WHERE event_id = :eid AND category_id = :cid
    """), {"eid": event_id, "cid": category_id})
    
    db.commit()
    return {"message": "Привязка к категории удалена"}