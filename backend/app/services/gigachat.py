import json
import httpx
import base64
import re
from datetime import datetime, timedelta
from app.config import settings

class GigaChatService:
    """Сервис для работы с GigaChat API"""
    
    def __init__(self):
        self.client_id = settings.GIGACHAT_CLIENT_ID
        self.secret = settings.GIGACHAT_SECRET
        self.scope = settings.GIGACHAT_SCOPE
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.api_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.access_token = None
        self.token_expires_at = None
    
    async def get_token(self):
        """Получает токен доступа"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        encoded = self.secret
        
        try:
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                response = await client.post(
                    self.auth_url,
                    headers={
                        "Authorization": f"Basic {encoded}",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                        "RqUID": "6f0b1291-c7f3-43c6-bb2e-9f3efb2dc98e"
                    },
                    data={"scope": self.scope}
                )
                
                if response.status_code != 200:
                    print(f"Ошибка получения токена: {response.status_code}")
                    return None
                
                data = response.json()
                self.access_token = data.get("access_token")
                expires_at = data.get("expires_at", 0)
                self.token_expires_at = datetime.fromtimestamp(expires_at / 1000) if expires_at else datetime.now() + timedelta(minutes=30)
                
                return self.access_token
        except Exception as e:
            print(f"Ошибка подключения к GigaChat: {e}")
            return None
    
    def _fix_broken_json(self, content: str) -> str:
        """Исправляет битый JSON от GigaChat (добавляет недостающие скобки)"""
        content = content.strip()
        
        # Убираем markdown
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Считаем открывающие и закрывающие скобки
        open_braces = content.count('{')
        close_braces = content.count('}')
        open_brackets = content.count('[')
        close_brackets = content.count(']')
        
        # Добавляем недостающие закрывающие скобки
        if open_braces > close_braces:
            content += '}' * (open_braces - close_braces)
        if open_brackets > close_brackets:
            content += ']' * (open_brackets - close_brackets)
        
        return content
    
    async def analyze_event(self, title: str, description: str):
        """Анализирует мероприятие через GigaChat и возвращает компетенции И категории"""
        token = await self.get_token()
        if not token:
            return []
        
        competences = [
            "Анализ информации",
            "Планирование",
            "Партнерство/сотрудничество",
            "Коммуникативная грамотность",
            "Клиентоориентированность",
            "Стрессоустойчивость",
            "Эмоциональный интеллект",
            "Ориентация на результат",
            "Саморазвитие",
            "Следование правилам",
            "Лидерство"
        ]
        
        categories = [
            "IT", "Спорт", "Наука", "Настольные игры",
            "Музыка", "Бизнес", "Искусство"
        ]
        
        prompt = f"""Ты — эксперт по анализу мероприятий для студентов. Проанализируй мероприятие.

НАЗВАНИЕ: {title}
ОПИСАНИЕ: {description if description else 'Отсутствует'}

Определи компетенции из списка: {', '.join(competences)}.
Определи категории из списка: {', '.join(categories)}.

Верни СТРОГО ТОЛЬКО JSON без текста:
{{"competences":[{{"name":"Название","relevance":5}}],"categories":[{{"name":"Название"}}]}}"""
        
        try:
            async with httpx.AsyncClient(verify=False, timeout=45) as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json={
                        "model": "GigaChat",
                        "messages": [
                            {"role": "system", "content": "Ты возвращаешь ТОЛЬКО валидный JSON. Никаких пояснений."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 300
                    }
                )
                
                if response.status_code != 200:
                    print(f"Ошибка GigaChat API: {response.status_code}")
                    return []
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # Исправляем битый JSON
                content = self._fix_broken_json(content)
                
                try:
                    result = json.loads(content)
                    if isinstance(result, list):
                        return result
                    return result
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга JSON от GigaChat: {e}")
                    print(f"Сырой ответ (исправленный): {content}")
                    return []
                
        except Exception as e:
            print(f"Ошибка анализа через GigaChat: {e}")
            return []