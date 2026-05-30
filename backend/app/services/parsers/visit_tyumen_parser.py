import re
import asyncio
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from app.services.parsers.base_parser import BaseParser


class VisitTyumenParser(BaseParser):
    def __init__(self, source_id: int):
        super().__init__(source_id, "VisitTyumen")
        self.base_url = "https://visittyumen.ru"
        self.events_url = f"{self.base_url}/events/"
    
    async def fetch_events(self) -> List[Dict[str, Any]]:
        events = []
        page = 1
        max_pages = 3
        
        while page <= max_pages:
            url = f"{self.events_url}?page={page}" if page > 1 else self.events_url
            print(f"Парсинг VisitTyumen страница {page}: {url}")
            
            html = await self.fetch_page(url)
            if not html:
                break
            
            soup = BeautifulSoup(html, 'lxml')
            cards = soup.select('div.events-content-card')
            print(f"Найдено карточек: {len(cards)}")
            
            if not cards:
                break
            
            for card in cards:
                try:
                    event_data = self.parse_card(card)
                    if event_data:
                        events.append(event_data)
                        print(f"  ✓ {event_data['title'][:50]}...")
                except Exception as e:
                    print(f"  ✗ Ошибка парсинга: {e}")
                    continue
            
            next_link = soup.select_one('.load_more a')
            if not next_link:
                break
            
            page += 1
            await asyncio.sleep(1)
        
        print(f"Всего собрано событий с VisitTyumen: {len(events)}")
        return events
    
    def parse_card(self, card) -> Optional[Dict[str, Any]]:
        title_elem = card.select_one('a.events-tabs-card-title')
        if not title_elem:
            return None
        
        title = self.clean_text(title_elem.text)
        if not title:
            return None
            
        url = title_elem.get('href', '')
        if url and not url.startswith('http'):
            url = self.base_url + url
        
        # Изображение
        image_url = None
        img_elem = card.select_one('img.events-tabs-image')
        if img_elem:
            image_url = img_elem.get('src', '')
            if image_url and not image_url.startswith('http'):
                image_url = self.base_url + image_url
        
        # Категория и город
        category = None
        city = 'Тюмень'
        info_spans = card.select('div.events-card-info-group span')
        if len(info_spans) >= 1:
            category = self.clean_text(info_spans[0].text)
        if len(info_spans) >= 3:
            city = self.clean_text(info_spans[-1].text)
        
        # Дата
        event_date = None
        date_elem = card.select_one('span.events-card-range-date')
        if date_elem:
            date_str = self.clean_text(date_elem.text)
            event_date = self.parse_date_range(date_str)
        
        # Цена
        price_type = None
        price_value = None
        price_elem = card.select_one('div.events-price-box span')
        if price_elem:
            price_text = self.clean_text(price_elem.text)
            price_type, price_value = self.extract_price(price_text)
        
        # Формат
        format_type = 'offline'
        if 'онлайн' in title.lower() or 'online' in title.lower():
            format_type = 'online'
        
        # Описание
        description = f"{title}. Категория: {category if category else 'разное'}. Место: {city}."
        desc_selectors = ['div[class*="description"]', 'div[class*="text"]', 'div[class*="body"]', 'p']
        for sel in desc_selectors:
            desc_elem = card.select_one(sel)
            if desc_elem:
                desc_text = self.clean_text(desc_elem.text)
                if desc_text and len(desc_text) > 30:
                    description = desc_text[:800]
                    break
        
        return {
            'title': title,
            'description': description,
            'url': url,
            'event_date': event_date,
            'location': city,
            'city': city,
            'format': format_type,
            'organizer': 'VisitTyumen',
            'image_url': image_url,
            'price_type': price_type,
            'price': str(price_value) if price_value else None,
            'source_id': self.source_id,
            'status': 'active',
            'category_name': category
        }