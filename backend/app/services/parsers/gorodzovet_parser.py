import httpx
import asyncio
import re
import random
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from app.services.parsers.base_parser import BaseParser


class GorodZovetParser(BaseParser):
    def __init__(self, source_id: int):
        super().__init__(source_id, "ГородЗовёт Тюмень")
        self.base_url = "https://gorodzovet.ru"
        self.city = "tyumen"
        self.main_url = f"{self.base_url}/{self.city}/"
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
        ]

    def _get_headers(self) -> dict:
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
        }

    async def fetch_events(self) -> List[Dict[str, Any]]:
        all_events = []
        seen_urls = set()

        print(f"\n📂 Главная: {self.main_url}")
        events = await self.parse_page(self.main_url)
        for event in events:
            if event['url'] not in seen_urls and event['url'] != '#':
                seen_urls.add(event['url'])
                all_events.append(event)
                print(f"  ✓ {event['title'][:50]}...")

        await asyncio.sleep(random.uniform(1, 2))

        categories = ['concert', 'theater', 'excursion', 'workshop', 'culture', 'kids', 'sport', 'music', 'shows', 'lifestyle', 'study']
        for cat in categories:
            cat_url = f"{self.main_url}{cat}/"
            print(f"\n📂 Категория: {cat_url}")
            events = await self.parse_page(cat_url)
            for event in events:
                if event['url'] not in seen_urls and event['url'] != '#':
                    seen_urls.add(event['url'])
                    all_events.append(event)
                    print(f"  ✓ {event['title'][:50]}...")
            await asyncio.sleep(random.uniform(1, 2))

        # Загружаем полные описания
        print(f"\n📝 Загружаем описания для {len(all_events)} мероприятий...")
        for i, event in enumerate(all_events):
            if event['url'] and event['url'] != '#':
                full_desc = await self.fetch_detail_description(event['url'])
                if full_desc:
                    event['description'] = full_desc
                    print(f"  [{i+1}/{len(all_events)}] ✓ {event['title'][:40]}...")
            await asyncio.sleep(random.uniform(0.3, 0.7))

        print(f"\nВсего собрано с ГородЗовёт: {len(all_events)}")
        return all_events

    async def parse_page(self, url: str) -> List[Dict[str, Any]]:
        events = []
        try:
            html = await self.fetch_page(url)
            if not html:
                return events

            soup = BeautifulSoup(html, 'lxml')
            cards = soup.select('div.event-block')
            print(f"  Карточек: {len(cards)}")

            for card in cards:
                event_data = self.parse_card(card)
                if event_data:
                    events.append(event_data)

        except Exception as e:
            print(f"  Ошибка: {e}")

        return events

    async def fetch_detail_description(self, url: str) -> Optional[str]:
        """Загружает детальную страницу и извлекает чистое описание"""
        try:
            html = await self.fetch_page(url)
            if not html:
                return None

            soup = BeautifulSoup(html, 'lxml')
            event_text = soup.select_one('div.eventText')
            if not event_text:
                return None

            # Собираем параграфы
            paragraphs = []
            service_words = [
                'стоимость', 'место проведения', 'библиотека', 'источник:',
                'изменить информацию', 'сообщить о проблеме', 'неправильная дата',
                'неправильный адрес', 'плохое описание', 'мероприятие отменено',
                'неприемлемый', 'нарушение авторских', 'это спам',
                'не получается купить', 'какая-то другая', 'это мое мероприятие',
                'обязательна предварительная запись',
            ]

            for elem in event_text.select('p'):
                text = self.clean_text(elem.text)
                if text and len(text) > 30:
                    lower = text.lower()
                    is_service = any(word in lower for word in service_words)
                    if not is_service:
                        paragraphs.append(text)

            if paragraphs:
                unique = list(dict.fromkeys(paragraphs))
                full_text = ' '.join(unique)
                if len(full_text) > 2000:
                    full_text = full_text[:2000] + '...'
                return full_text

            # Fallback: весь текст до маркера
            full_text = self.clean_text(event_text.get_text())
            cut_markers = ['Стоимость', 'Место проведения', 'Библиотека', 'Источник:', 'изменить информацию']
            for marker in cut_markers:
                idx = full_text.find(marker)
                if idx > 100:
                    full_text = full_text[:idx].strip()
                    break

            if len(full_text) > 2000:
                full_text = full_text[:2000] + '...'
            return full_text if len(full_text) > 20 else None

        except Exception as e:
            print(f"    ⚠️ Ошибка загрузки описания: {e}")
        return None

    def parse_card(self, card) -> Optional[Dict[str, Any]]:
        title_elem = card.select_one('h3 span') or card.select_one('h3')
        if not title_elem:
            return None
        title = self.clean_text(title_elem.text)
        if not title or len(title) < 3:
            return None

        link_elem = card.select_one('a[href*="-event"]') or card.select_one('div.innlink[data-link]')
        url = ''
        if link_elem:
            url = link_elem.get('href', '') or link_elem.get('data-link', '')
        if url and not url.startswith('http'):
            url = self.base_url + url

        image_url = None
        img_elem = card.select_one('img')
        if img_elem:
            image_url = img_elem.get('src') or img_elem.get('data-src')

        event_date = None
        months_map = {
            'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'май': 5, 'мая': 5,
            'июн': 6, 'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12,
        }
        date_elems = card.select('div.event-date-one')
        if date_elems:
            for date_elem in date_elems[:2]:
                day_elem = date_elem.select_one('span.event-day')
                month_elem = date_elem.select_one('a.event-month')
                if day_elem and month_elem:
                    day_str = self.clean_text(day_elem.text).strip()
                    month_str = self.clean_text(month_elem.text).strip().lower()
                    if month_str in months_map:
                        try:
                            day = int(day_str)
                            month = months_map[month_str]
                            year = datetime.now().year
                            event_date = datetime(year, month, day, 14, 0)
                            if event_date < datetime.now():
                                event_date = datetime(year + 1, month, day, 14, 0)
                            break
                        except (ValueError, IndexError):
                            pass

        description = title
        desc_selectors = ['div.lines10', 'div.lines4', 'div.lines6', 'div.lines8', 'div[class*="lines"]']
        for sel in desc_selectors:
            desc_elem = card.select_one(sel)
            if desc_elem:
                desc_text = self.clean_text(desc_elem.text)
                if desc_text and len(desc_text) > 20:
                    description = desc_text[:500]
                    break

        price_type = None
        price_value = None
        price_elem = card.select_one('div.event-price')
        if price_elem:
            price_text = self.clean_text(price_elem.text)
            numbers = re.findall(r'\d+', price_text)
            if numbers:
                price_type = 'from'
                price_value = int(numbers[0])
        badge_elem = card.select_one('div.event-badge')
        if badge_elem and 'бесплатно' in self.clean_text(badge_elem.text).lower():
            price_type = 'free'

        category_name = None
        tag_elems = card.select('div.event-tags a.tag')
        if tag_elems:
            category_name = self.clean_text(tag_elems[0].text)

        location = "Тюмень"
        venue_elem = card.select_one('a.seance-venue-name, a.event-object-name')
        if venue_elem:
            location = self.clean_text(venue_elem.text)

        format_type = 'offline'
        if 'онлайн' in title.lower() or 'online' in title.lower():
            format_type = 'online'

        return {
            'title': title,
            'description': description,
            'url': url if url else '#',
            'event_date': event_date,
            'location': location,
            'city': 'Тюмень',
            'format': format_type,
            'organizer': 'ГородЗовёт',
            'image_url': image_url,
            'price_type': price_type,
            'price': str(price_value) if price_value else None,
            'source_id': self.source_id,
            'status': 'active',
            'category_name': category_name
        }