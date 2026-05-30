import re
import asyncio
import json
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from app.services.parsers.base_parser import BaseParser


class MoiPortalParser(BaseParser):
    """Парсер мероприятий с сайта moi-portal.ru"""
    
    def __init__(self, source_id: int):
        super().__init__(source_id, "Мой-портал.ру")
        self.base_url = "https://xn----8sbzkbmchku.xn--p1ai"
        self.afisha_url = f"{self.base_url}/kuda-skhodit/"
        
        # Маппинг ID категорий в названия
        self.category_map = {
            '671290': 'Мастер-классы и интенсивы',
            '671280': 'Лекции',
            '671283': 'Концерты',
            '671288': 'Спектакли',
            '686619': 'Встреча',
            '693886': 'Стендап',
            '730051': 'Маркет',
            '736301': 'Разное',
        }
        
        # Маппинг месяцев
        self.months_map = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
            'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
            'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
        }
    
    async def fetch_events(self) -> List[Dict[str, Any]]:
        """Парсит мероприятия с раздела 'Куда сходить'"""
        all_events = []
        seen_urls = set()
        
        # Шаг 1: Собираем ссылки на все дайджесты с главной страницы
        digest_urls = await self.fetch_digest_urls()
        print(f"\n📋 Найдено дайджестов: {len(digest_urls)}")
        
        # Шаг 2: Парсим каждый дайджест для извлечения конкретных мероприятий
        for i, digest_url in enumerate(digest_urls, 1):
            print(f"\n📄 [{i}/{len(digest_urls)}] Парсинг дайджеста: {digest_url}")
            
            try:
                events = await self.parse_digest_page(digest_url)
                
                new_count = 0
                for event in events:
                    # Уникальность по названию + дате
                    event_key = f"{event['title']}_{event['event_date']}"
                    if event_key not in seen_urls:
                        seen_urls.add(event_key)
                        all_events.append(event)
                        new_count += 1
                
                print(f"  ✓ Извлечено мероприятий: {len(events)} (новых: {new_count})")
                
            except Exception as e:
                print(f"  ❌ Ошибка парсинга дайджеста: {e}")
                continue
            
            # Задержка между запросами
            await asyncio.sleep(0.5)
        
        print(f"\n📊 Всего собрано мероприятий с Мой-портал.ру: {len(all_events)}")
        return all_events
    
    async def fetch_digest_urls(self) -> List[str]:
        """Собирает ссылки на все дайджесты с главной страницы и через AJAX"""
        digest_urls = []
        
        # Парсим основную страницу
        html = await self.fetch_page(self.afisha_url)
        if html:
            urls = self.extract_digest_urls_from_html(html)
            digest_urls.extend(urls)
            print(f"  ✓ Собрано ссылок с главной: {len(urls)}")
        
        # Пробуем загрузить ещё страницы через AJAX
        page = 2
        max_pages = 3
        
        while page <= max_pages:
            ajax_url = f"{self.afisha_url}?AJAX=Y&PAGEN_1={page}"
            print(f"  📄 Загрузка AJAX страницы {page}...")
            
            html_ajax = await self.fetch_page(ajax_url)
            if not html_ajax:
                break
            
            urls = self.extract_digest_urls_from_html(html_ajax)
            if not urls:
                break
            
            digest_urls.extend(urls)
            print(f"  ✓ Собрано ссылок со страницы {page}: {len(urls)}")
            page += 1
            await asyncio.sleep(0.5)
        
        return digest_urls
    
    def extract_digest_urls_from_html(self, html: str) -> List[str]:
        """Извлекает ссылки на дайджесты из HTML"""
        urls = []
        soup = BeautifulSoup(html, 'lxml')
        
        # Ищем ссылки в карточках article-preview-card
        cards = soup.select('a.article-preview-card')
        for card in cards:
            href = card.get('href', '')
            if href and '/kuda-skhodit/' in href and not href.endswith('/kuda-skhodit/'):
                if href.startswith('/'):
                    href = self.base_url + href
                if href not in urls:
                    urls.append(href)
        
        return urls
    
    async def parse_digest_page(self, url: str) -> List[Dict[str, Any]]:
        """Парсит страницу дайджеста и извлекает отдельные мероприятия"""
        events = []
        
        html = await self.fetch_page(url)
        if not html:
            return events
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Находим все блоки с датами (1 мая, 2 мая и т.д.)
        date_blocks = soup.select('div.events-list__date-item')
        
        if not date_blocks:
            print(f"    ⚠️ Блоки с датами не найдены")
            return events
        
        print(f"    Найдено блоков с датами: {len(date_blocks)}")
        
        for date_block in date_blocks:
            # Извлекаем дату из заголовка блока
            date_text = ''
            date_control = date_block.select_one('span.events-list__date-control-text')
            if date_control:
                date_text = self.clean_text(date_control.text)
            
            # Парсим дату
            base_date = self.parse_simple_date(date_text)
            
            # Находим все мероприятия внутри этого блока
            event_items = date_block.select('div.events-list__event-item')
            
            for item in event_items:
                event_data = self.parse_event_item(item, base_date, url)
                if event_data:
                    events.append(event_data)
                    print(f"    ✓ {event_data['title'][:60]}...")
        
        return events
    
    def parse_event_item(self, item, base_date: Optional[datetime], source_url: str) -> Optional[Dict[str, Any]]:
        """Парсит одно мероприятие из дайджеста"""
        
        # Название
        title_elem = item.select_one('span.events-list__event-item-title')
        if not title_elem:
            return None
        
        title = self.clean_text(title_elem.text)
        if not title or len(title) < 3:
            return None
        
        # Удаляем возрастное ограничение из названия (12+), (16+) и т.д.
        title = re.sub(r'\s*\(\d+\+\)\s*$', '', title).strip()
        
        # Время
        time_str = ''
        time_elem = item.select_one('span.events-list__event-item-time')
        if time_elem:
            time_str = self.clean_text(time_elem.text)
        
        # Объединяем дату и время
        event_date = base_date
        if event_date and time_str:
            try:
                time_parts = time_str.split(':')
                if len(time_parts) == 2:
                    hours, minutes = int(time_parts[0]), int(time_parts[1])
                    event_date = event_date.replace(hour=hours, minute=minutes)
            except (ValueError, IndexError):
                pass
        
        # Цена
        price_type = None
        price_value = None
        price_elem = item.select_one('span.events-list__event-item-cat')
        if price_elem:
            price_text = self.clean_text(price_elem.text)
            if 'бесплатно' in price_text.lower():
                price_type = 'free'
            else:
                price_type, price_value = self.extract_price(price_text)
        
        # Описание (в раскрывающемся блоке)
        description = ''
        desc_elem = item.select_one('div.events-list__item-info')
        if desc_elem:
            description = self.clean_text(desc_elem.text)
        
        if not description:
            description = f"Мероприятие: {title}"
        
        # Ссылка на билеты / регистрацию
        ticket_url = None
        ticket_link = item.select_one('a.events-list__item-link')
        if ticket_link:
            ticket_url = ticket_link.get('href', '')
        
        # Категория
        category = None
        filter_type = item.get('data-filter-type', '')
        if filter_type and filter_type != 'all' and filter_type != 'free':
            category = self.category_map.get(filter_type, filter_type)
        
        # Изображение (обычно дефолтное, но может быть и специфичное)
        image_url = None
        img_elem = item.select_one('div.events-list__item-fig img')
        if img_elem:
            src = img_elem.get('src', '')
            if src and 'project-afisha-default' not in src:
                image_url = src
                if image_url.startswith('/'):
                    image_url = self.base_url + image_url
        
        # Формат
        format_type = 'offline'
        full_text = (title + ' ' + description).lower()
        if 'онлайн' in full_text or 'online' in full_text:
            format_type = 'online'
        
        # Местоположение (пытаемся извлечь из описания)
        location = self.extract_location_from_description(description)
        
        return {
            'title': title[:200],
            'description': description[:500],
            'url': ticket_url if ticket_url else source_url,  # Ссылка на билеты или на дайджест
            'event_date': event_date,
            'location': location,
            'city': 'Тюмень',
            'format': format_type,
            'organizer': 'Мой-портал.ру',
            'image_url': image_url,
            'price_type': price_type,
            'price': str(price_value) if price_value else None,
            'source_id': self.source_id,
            'status': 'active',
            'category_name': category
        }
    
    def parse_simple_date(self, date_text: str) -> Optional[datetime]:
        """Парсит простую дату вида '1 мая'"""
        if not date_text:
            return None
        
        today = datetime.now()
        
        # Ищем паттерн "число месяц"
        match = re.search(r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)', date_text.lower())
        if match:
            try:
                day = int(match.group(1))
                month = self.months_map[match.group(2)]
                year = today.year
                dt = datetime(year, month, day)
                # Если дата в прошлом, используем следующий год
                if dt < today:
                    dt = datetime(year + 1, month, day)
                return dt
            except (ValueError, KeyError):
                pass
        
        return None
    
    def extract_location_from_description(self, description: str) -> str:
        """Извлекает место проведения из описания"""
        location = "Тюмень"
        
        # Паттерны для поиска адреса
        patterns = [
            r'Где:\s*([^\.\n]+)',
            r'Место:\s*([^\.\n]+)',
            r'Адрес:\s*([^\.\n]+)',
            r'по адресу\s*([^\.\n]+)',
            r'ул\.\s*([^,\.\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                loc = self.clean_text(match.group(1))
                if loc and len(loc) > 3:
                    return loc
        
        return location