import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('parser_output.txt', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.services.parsers.gorodzovet_parser import GorodZovetParser
from app.services.parsers.visit_tyumen_parser import VisitTyumenParser
from app.services.parsers.vk_parser import VKParser
from app.services.parsers.moi_portal_parser import MoiPortalParser
from app.services.gigachat import GigaChatService

async def run_parser():
    """Запускает парсинг всех активных источников"""
    
    logger.info("=" * 60)
    logger.info(f"🚀 Запуск парсера мероприятий: {datetime.now()}")
    logger.info("=" * 60)
    
    stats = {
        "total_sources": 0,
        "total_events_fetched": 0,
        "total_events_added": 0,
        "total_ai_success": 0,
        "total_ai_failed": 0,
        "errors": []
    }
    
    db = SessionLocal()
    gigachat = GigaChatService()
    
    logger.info("\n📡 Проверка подключения к GigaChat API...")
    token = await gigachat.get_token()
    if token:
        logger.info("✅ GigaChat API подключен успешно")
    else:
        logger.warning("⚠️ GigaChat API недоступен")
    
    try:
        sources = db.execute(text("""
            SELECT id, name, url, parser_type 
            FROM sources 
            WHERE is_active = true AND parser_type IN ('html_parser', 'vk_api')
            ORDER BY id
        """)).fetchall()
        
        stats["total_sources"] = len(sources)
        logger.info(f"\n📊 Найдено активных источников: {len(sources)}")
        
        for source in sources:
            source_id, source_name, source_url, parser_type = source
            
            logger.info(f"\n{'='*50}")
            logger.info(f"📌 Обработка источника: {source_name}")
            logger.info(f"   ID: {source_id}")
            logger.info(f"{'='*50}")
            
            parser = None
            
            if source_id == 1:
                parser = VKParser(source_id, source_name, "tochkatyumen")
                logger.info("🔧 VKParser (Точка кипения)")
            elif source_id == 2:
                parser = VKParser(source_id, source_name, "utmn_career")
                logger.info("🔧 VKParser (Центр карьеры)")
            elif source_id == 3:
                parser = GorodZovetParser(source_id)
                logger.info("🔧 GorodZovetParser")
            elif source_id == 4:
                parser = VisitTyumenParser(source_id)
                logger.info("🔧 VisitTyumenParser")
            elif source_id == 5:
                parser = MoiPortalParser(source_id)
                logger.info("🔧 MoiPortalParser")
            else:
                continue
            
            if parser:
                try:
                    events_data = await parser.fetch_events()
                    stats["total_events_fetched"] += len(events_data)
                    logger.info(f"📦 Получено событий: {len(events_data)}")
                    
                    new_events = 0
                    
                    for idx, e_data in enumerate(events_data, 1):
                        try:
                            logger.info(f"\n  [{idx}/{len(events_data)}] 📝 {e_data['title'][:60]}...")
                            
                            existing = db.execute(text("""
                                SELECT id FROM events 
                                WHERE url = :url AND source_id = :sid
                            """), {"url": e_data['url'], "sid": source_id}).fetchone()
                            
                            if existing:
                                logger.info(f"    ↳ Уже существует (ID: {existing[0]})")
                                continue
                            
                            location = e_data.get('location', 'Тюмень')
                            city = e_data.get('city', '')
                            if city and city not in location:
                                location = f"{city}, {location}"
                            
                            result = db.execute(text("""
                                INSERT INTO events 
                                (title, description, url, source_id, event_date, location, format, image_url, status)
                                VALUES (:t, :d, :u, :s, :ed, :l, :f, :i, 'active')
                                RETURNING id
                            """), {
                                "t": e_data['title'], "d": e_data.get('description', ''),
                                "u": e_data['url'], "s": source_id,
                                "ed": e_data.get('event_date'), "l": location,
                                "f": e_data.get('format', 'offline'), "i": e_data.get('image_url')
                            })
                            
                            event_id = result.fetchone()[0]
                            db.commit()
                            new_events += 1
                            stats["total_events_added"] += 1
                            logger.info(f"    ✅ Добавлено (ID: {event_id})")
                            
                            if e_data.get('category_name'):
                                cat_result = db.execute(text("""
                                    SELECT id FROM categories WHERE name = :n
                                """), {"n": e_data['category_name']}).fetchone()
                                if cat_result:
                                    db.execute(text("""
                                        INSERT INTO event_categories (event_id, category_id)
                                        VALUES (:e, :c) ON CONFLICT DO NOTHING
                                    """), {"e": event_id, "c": cat_result[0]})
                                    db.commit()
                                    logger.info(f"    📂 {e_data['category_name']}")
                            
                            if token:
                                logger.info(f"    🤖 GigaChat...")
                                try:
                                    analysis = await asyncio.wait_for(
                                        parser.enrich_with_ai(e_data), timeout=45.0
                                    )
                                    
                                    if analysis and isinstance(analysis, dict):
                                        comps = analysis.get('competences', [])
                                        cats = analysis.get('categories', [])
                                        
                                        if comps:
                                            logger.info(f"    📋 Компетенций: {len(comps)}")
                                            stats["total_ai_success"] += 1
                                            for c in comps:
                                                comp = db.execute(text("""
                                                    SELECT id FROM competences WHERE name = :n
                                                """), {"n": c.get('name')}).fetchone()
                                                if comp:
                                                    try:
                                                        db.execute(text("""
                                                            INSERT INTO event_competences (event_id, competence_id, relevance)
                                                            VALUES (:e, :c, :r)
                                                            ON CONFLICT (event_id, competence_id) DO UPDATE SET relevance = EXCLUDED.relevance
                                                        """), {"e": event_id, "c": comp[0], "r": c.get('relevance', 3)})
                                                        db.commit()
                                                        logger.info(f"      • {c.get('name')}: {c.get('relevance')}")
                                                    except Exception:
                                                        db.rollback()
                                        
                                        if cats:
                                            logger.info(f"    📂 Категорий: {len(cats)}")
                                            for c in cats:
                                                cat = db.execute(text("""
                                                    SELECT id FROM categories WHERE name = :n
                                                """), {"n": c.get('name')}).fetchone()
                                                if cat:
                                                    try:
                                                        db.execute(text("""
                                                            INSERT INTO event_categories (event_id, category_id)
                                                            VALUES (:e, :c) ON CONFLICT DO NOTHING
                                                        """), {"e": event_id, "c": cat[0]})
                                                        db.commit()
                                                        logger.info(f"      • {c.get('name')}")
                                                    except Exception:
                                                        db.rollback()
                                    else:
                                        stats["total_ai_failed"] += 1
                                except asyncio.TimeoutError:
                                    logger.warning(f"    ⏱️ Таймаут")
                                    stats["total_ai_failed"] += 1
                                except Exception as e:
                                    logger.warning(f"    ⚠️ {type(e).__name__}")
                                    stats["total_ai_failed"] += 1
                                    db.rollback()
                            
                            await asyncio.sleep(0.3)
                            
                        except Exception as e:
                            logger.error(f"    ❌ Ошибка: {type(e).__name__}")
                            db.rollback()
                            continue
                    
                    logger.info(f"\n📈 {source_name}: +{new_events} новых")
                    
                except Exception as e:
                    logger.error(f"❌ {source_name}: {str(e)[:100]}")
                    stats["errors"].append(str(e)[:100])
                    db.rollback()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 ПАРСИНГ ЗАВЕРШЕН!")
        logger.info(f"📊 Источников: {stats['total_sources']} | Собрано: {stats['total_events_fetched']} | Новых: {stats['total_events_added']} | AI: {stats['total_ai_success']}/{stats['total_ai_success'] + stats['total_ai_failed']}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_parser())