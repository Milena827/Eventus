import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.parsers.base_parser import BaseParser
from app.config import settings

try:
    import vk_api
except ImportError:
    vk_api = None
    print("⚠️ vk_api не установлен. VK парсер не будет работать.")


class VKParser(BaseParser):
    """Парсер мероприятий из сообществ ВКонтакте через VK API"""
    
    def __init__(self, source_id: int, source_name: str, group_domain: str):
        super().__init__(source_id, source_name)
        self.group_domain = group_domain
        self.vk_session = None
        self.vk = None
        self.group_id = None
        
        if vk_api and settings.VK_ACCESS_TOKEN and settings.VK_ACCESS_TOKEN != 'ваш_vk_токен':
            try:
                self.vk_session = vk_api.VkApi(token=settings.VK_ACCESS_TOKEN)
                self.vk = self.vk_session.get_api()
                print(f"✅ VK API инициализирован для {group_domain}")
            except Exception as e:
                print(f"❌ Ошибка инициализации VK API: {e}")
        else:
            print(f"⚠️ VK API недоступен (нет токена или библиотеки)")
    
    async def fetch_events(self) -> List[Dict[str, Any]]:
        if not self.vk:
            print(f"⚠️ VK API недоступен для {self.group_domain}")
            return []
        
        if not self.group_id:
            try:
                group_info = self.vk.groups.getById(group_id=self.group_domain)
                if group_info:
                    self.group_id = group_info[0]['id']
                    print(f"✅ Группа {self.group_domain} (ID: {self.group_id})")
            except Exception as e:
                print(f"❌ Ошибка получения ID группы {self.group_domain}: {e}")
                return []
        
        all_events = []
        
        try:
            response = self.vk.wall.get(
                owner_id=-self.group_id,
                count=100,
                filter='owner',
                extended=1
            )
            
            posts = response.get('items', [])
            print(f"📥 Получено постов из VK ({self.group_domain}): {len(posts)}")
            
            skipped_no_date = 0
            skipped_no_keyword = 0
            
            for post in posts:
                event_data = self.parse_wall_post(post)
                if event_data:
                    all_events.append(event_data)
                    print(f"  ✓ {event_data['title'][:60]}...")
                    self._log_parsed_fields(event_data, 'VK')
            
            print(f"📊 Статистика VK ({self.group_domain}):")
            print(f"   • Всего постов: {len(posts)}")
            print(f"   • Мероприятий: {len(all_events)}")
            print(f"   • Пропущено (нет даты): {skipped_no_date}")
            print(f"   • Пропущено (не анонс): {skipped_no_keyword}")
            
        except Exception as e:
            print(f"❌ Ошибка получения постов из VK: {e}")
        
        return all_events
    
    def parse_wall_post(self, post: dict) -> Optional[Dict[str, Any]]:
        text = post.get('text', '').strip()
        if not text:
            return None
        
        lines = text.split('\n')
        title_line = ''
        for line in lines:
            cleaned = self.clean_text(line)
            if cleaned and len(cleaned) > 5:
                title_line = cleaned
                break
        
        if not title_line:
            return None
        
        is_event, reason = self.is_event_post(text, title_line)
        if not is_event:
            return None
        
        description = text[:500]
        
        event_date = self.extract_date_from_text(text)
        if not event_date:
            return None
        
        image_url = None
        attachments = post.get('attachments', [])
        for attachment in attachments:
            if attachment['type'] == 'photo':
                sizes = attachment['photo'].get('sizes', [])
                if sizes:
                    image_url = sizes[-1].get('url')
                    break
        
        post_id = post.get('id')
        owner_id = post.get('owner_id')
        url = f"https://vk.com/wall{owner_id}_{post_id}"
        
        format_type = 'offline'
        if 'онлайн' in text.lower() or 'online' in text.lower():
            format_type = 'online'
        
        location = self.extract_location(text) or "Тюмень"
        
        return {
            'title': title_line[:200],
            'description': description,
            'url': url,
            'event_date': event_date,
            'location': location,
            'format': format_type,
            'organizer': self.source_name,
            'image_url': image_url,
            'price_type': None,
            'price': None,
            'source_id': self.source_id,
            'status': 'active',
            'category_name': None
        }
    
    def is_event_post(self, text: str, title: str) -> tuple:
        event_keywords = [
            'мероприятие', 'анонс', 'приглашаем', 'состоится',
            'встреча', 'лекция', 'семинар', 'мастер-класс', 'вебинар',
            'конференция', 'форум', 'фестиваль', 'выставка', 'экскурсия',
            'концерт', 'спектакль', 'тренинг', 'воркшоп', 'хакатон',
            'открытие', 'презентация', 'показ', 'обсуждение',
            '🏃', '🎯', '🎪', '🎭', '🎨', '🎬', '🎤', '🎧',
            '📅', '📆', '🗓', '📍',
            'регистрация', 'участие', 'билеты', 'вход свободный',
            'будет проходить', 'пройдёт', 'приглашаются', 'ждём'
        ]
        
        date_patterns = [
            r'\d{1,2}\.\d{1,2}',
            r'\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)',
            r'\d{1,2}\s+(янв|фев|мар|апр|мая|июн|июл|авг|сен|окт|ноя|дек)',
        ]
        
        has_date = any(re.search(pattern, text.lower()) for pattern in date_patterns)
        has_keyword = any(keyword in text.lower() for keyword in event_keywords)
        
        return (has_date and has_keyword), f"date={has_date}, keyword={has_keyword}"
    
    def extract_date_from_text(self, text: str) -> Optional[datetime]:
        if not text:
            return None
        
        text_lower = text.lower()
        today = datetime.now()
        
        months_map = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
            'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
            'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
        }
        
        # Формат "21 апреля 2026"
        for month_name, month_num in months_map.items():
            pattern = r'(\d{1,2})\s+' + month_name + r'(?:\s+(\d{4}))?'
            match = re.search(pattern, text_lower)
            if match:
                day = int(match.group(1))
                year = int(match.group(2)) if match.group(2) else today.year
                try:
                    dt = datetime(year, month_num, day)
                    if dt < today and not match.group(2):
                        dt = datetime(year + 1, month_num, day)
                    return dt
                except ValueError:
                    continue
        
        # Формат "21.04.2026" или "21.04"
        pattern = r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?'
        match = re.search(pattern, text)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3)) if match.group(3) else today.year
            try:
                dt = datetime(year, month, day)
                if dt < today and not match.group(3):
                    dt = datetime(year + 1, month, day)
                return dt
            except ValueError:
                pass
        
        return None
    
    def extract_location(self, text: str) -> Optional[str]:
        location_patterns = [
            r'📍\s*([^\n]+)',
            r'место[:\s]+([^\n\.]+)',
            r'локация[:\s]+([^\n\.]+)',
            r'адрес[:\s]+([^\n\.]+)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = self.clean_text(match.group(1))
                if location and len(location) > 3:
                    return location
        
        return None