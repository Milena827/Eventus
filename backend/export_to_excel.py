"""
Экспорт мероприятий из БД в Excel
Запуск: python export_to_excel.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    # Запрос всех мероприятий с информацией об источниках
    query = """
        SELECT 
            e.id,
            e.title,
            e.description,
            e.url,
            e.event_date,
            e.location,
            e.format,
            e.image_url,
            e.status,
            s.name as source_name,
            s.url as source_url,
            s.parser_type
        FROM events e
        JOIN sources s ON e.source_id = s.id
        ORDER BY e.event_date DESC, e.id DESC
    """
    
    result = db.execute(text(query))
    rows = result.fetchall()
    
    # Создаём DataFrame
    df = pd.DataFrame(rows, columns=[
        'ID',
        'Название',
        'Описание',
        'Ссылка',
        'Дата мероприятия',
        'Место',
        'Формат',
        'Изображение',
        'Статус',
        'Источник',
        'URL источника',
        'Тип парсера'
    ])
    
    # Форматируем даты
    df['Дата мероприятия'] = pd.to_datetime(df['Дата мероприятия']).dt.strftime('%d.%m.%Y %H:%M')
    
    # Сохраняем в Excel
    filename = 'events_export.xlsx'
    df.to_excel(filename, index=False, engine='openpyxl')
    
    print(f"✅ Экспортировано {len(df)} мероприятий в файл {filename}")
    print(f"\n📊 Статистика по источникам:")
    print(df['Источник'].value_counts().to_string())

except Exception as e:
    print(f"❌ Ошибка: {e}")
finally:
    db.close()