from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

# ============================================
# USER SCHEMAS
# ============================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    course: int = Field(..., ge=1, le=6)
    faculty: str
    specialty: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    course: Optional[int] = Field(None, ge=1, le=6)
    faculty: Optional[str] = None
    specialty: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    course: int
    faculty: str
    specialty: Optional[str]
    created_at: datetime

# ============================================
# EVENT SCHEMAS
# ============================================

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    location: Optional[str] = None
    city: Optional[str] = "Тюмень"
    format: str = "offline"
    organizer: Optional[str] = None
    image_url: Optional[str] = None
    price_type: Optional[str] = None
    price: Optional[str] = None

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    location: Optional[str] = None
    city: Optional[str] = "Тюмень"
    format: str = "offline"
    organizer: Optional[str] = None
    image_url: Optional[str] = None
    price_type: Optional[str] = None
    price: Optional[str] = None
    url: Optional[str] = None
    source_id: Optional[int] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    location: Optional[str] = None
    format: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None

class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    event_date: Optional[datetime]
    location: Optional[str]
    format: str
    image_url: Optional[str]
    status: str
    url: Optional[str] = None
    source_id: Optional[int] = None
    source_name: Optional[str] = None
    competences: List[dict] = []
    categories: List[dict] = []
    
    class Config:
        from_attributes = True

# ============================================
# TEST RESULTS SCHEMAS
# ============================================

class TestResultCreate(BaseModel):
    competence_id: int
    score: int = Field(..., ge=200, le=800)

class TestResultUpdate(BaseModel):
    score: int = Field(..., ge=200, le=800)

class TestResultResponse(BaseModel):
    competence_id: int
    competence_name: str
    description: Optional[str]
    score: int

# ============================================
# INTERESTS SCHEMAS
# ============================================

class InterestCreate(BaseModel):
    category_id: int
    weight: int = Field(1, ge=1, le=5)

class InterestUpdate(BaseModel):
    weight: int = Field(..., ge=1, le=5)

class InterestResponse(BaseModel):
    category_id: int
    category_name: str
    weight: int

# ============================================
# USER PROFILE SCHEMAS
# ============================================

class UserFullProfileResponse(BaseModel):
    user: UserResponse
    test_results: List[TestResultResponse] = []
    interests: List[InterestResponse] = []

# ============================================
# RECOMMENDATIONS SCHEMAS
# ============================================

class RecommendationEventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    event_date: Optional[datetime]
    location: Optional[str]
    city: Optional[str]
    format: str
    organizer: Optional[str]
    image_url: Optional[str]
    price_type: Optional[str]
    price: Optional[str]
    relevance: Optional[int] = None
    competence_score: Optional[int] = None
    interest_weight: Optional[int] = None

class RecommendationResponse(BaseModel):
    competence_based: List[dict]
    interest_based: List[dict]

# ============================================
# USER ACTION SCHEMAS
# ============================================

class UserActionCreate(BaseModel):
    event_id: int
    action_type: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None

class UserActionResponse(BaseModel):
    id: int
    event_id: int
    event_title: str
    action_type: str
    rating: Optional[int]
    review_text: Optional[str]
    created_at: datetime

# ============================================
# COMPETENCE SCHEMAS
# ============================================

class CompetenceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

class CategoryResponse(BaseModel):
    id: int
    name: str

class ValidationError(BaseModel):
    loc: List[str]
    msg: str
    type: str

class HTTPValidationError(BaseModel):
    detail: List[ValidationError]

class HealthResponse(BaseModel):
    status: str

class RootResponse(BaseModel):
    message: str
    status: str

class SourceResponse(BaseModel):
    id: int
    name: str
    url: str
    parser_type: str
    is_active: bool

class ParserStatsResponse(BaseModel):
    total_sources: int
    total_events_fetched: int
    total_events_added: int
    errors: List[str] = []