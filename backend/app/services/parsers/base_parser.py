import httpx
import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod
from app.services.gigachat import GigaChatService


class BaseParser(ABC):
    def __init__(self, source_id: int, source_name: str):
        self.source_id = source_id
        self.source_name = source_name
        self.gigachat = GigaChatService()
    
    @abstractmethod
    async def fetch_events(self) -> List[Dict[str, Any]]:
        pass
    
    async def fetch_page(self, url: str) -> Optional[str]:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(
                    timeout=30.0,
                    follow_redirects=True,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
            except Exception as e:
                print(f"Попытка {attempt + 1} не удалась для {url}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        return None
    
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Удаляем эмодзи и спецсимволы, но оставляем буквы, цифры и основные знаки
        text = re.sub(r'[^\w\s.,!?:;@\-–—«»"\'()\[\]\/№#&]', '', text)
        # Удаляем множественные пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def parse_date_range(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        
        date_str = date_str.lower().strip()
        today = datetime.now()
        
        months = {
            'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'май': 5, 'мая': 5,
            'июн': 6, 'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12,
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'июня': 6,
            'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
        }
        
        try:
            # Формат: "21.04.2026" или "21.04"
            if re.search(r'\d{1,2}\.\d{1,2}', date_str):
                match = re.search(r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?', date_str)
                if match:
                    day = int(match.group(1))
                    month = int(match.group(2))
                    year = int(match.group(3)) if match.group(3) else today.year
                    dt = datetime(year, month, day)
                    if dt < today and not match.group(3):
                        dt = datetime(year + 1, month, day)
                    return dt
            
            # Формат: "25 марта" или "25 марта 2026"
            for month_name, month_num in months.items():
                if month_name in date_str:
                    match = re.search(r'(\d{1,2})\s*' + month_name + r'(?:\s*(\d{4}))?', date_str)
                    if match:
                        day = int(match.group(1))
                        year = int(match.group(2)) if match.group(2) else today.year
                        dt = datetime(year, month_num, day)
                        if dt < today and not match.group(2):
                            dt = datetime(year + 1, month_num, day)
                        return dt
            
            # Формат ISO: "2026-04-21T18:00:00"
            iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
            if iso_match:
                return datetime(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
                    
        except Exception as e:
            print(f"⚠️ Ошибка парсинга даты '{date_str}': {e}")
        
        return None
    
    def extract_price(self, price_text: str) -> tuple:
        if not price_text:
            return None, None
        
        price_text = price_text.lower().strip()
        
        if 'бесплатно' in price_text or 'free' in price_text:
            return 'free', None
        
        numbers = re.findall(r'[\d\s]+', price_text.replace('\xa0', ' '))
        if numbers:
            price_value = numbers[0].replace(' ', '')
            if 'от' in price_text:
                return 'from', int(price_value) if price_value.isdigit() else None
            else:
                return 'fixed', int(price_value) if price_value.isdigit() else None
        
        return None, None
    
    async def enrich_with_ai(self, event_data: Dict[str, Any]) -> List[Dict]:
        try:
            analysis = await self.gigachat.analyze_event(
                title=event_data.get('title', ''),
                description=event_data.get('description', '')
            )
            return analysis
        except Exception as e:
            print(f"Ошибка AI анализа: {e}")
            return []
    
    def _log_parsed_fields(self, event_data: Dict[str, Any], source: str):
        """Логирует качество парсинга для отладки"""
        fields_status = []
        
        if event_data.get('title'):
            fields_status.append(f"✅ title")
        else:
            fields_status.append(f"❌ title")
        
        if event_data.get('event_date'):
            fields_status.append(f"✅ date")
        else:
            fields_status.append(f"⚠️ date=NULL")
        
        if event_data.get('location') and event_data['location'] != 'Тюмень':
            fields_status.append(f"✅ location")
        else:
            fields_status.append(f"⚠️ location=default")
        
        if event_data.get('image_url'):
            fields_status.append(f"✅ image")
        else:
            fields_status.append(f"⚠️ image=NULL")
        
        if event_data.get('description') and len(event_data.get('description', '')) > 20:
            fields_status.append(f"✅ desc({len(event_data['description'])}chars)")
        else:
            fields_status.append(f"⚠️ desc=short")
        
        print(f"    📊 [{source}] " + " | ".join(fields_status))