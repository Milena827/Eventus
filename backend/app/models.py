from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    course = Column(Integer, CheckConstraint('course BETWEEN 1 AND 6'))
    faculty = Column(String(255))
    specialty = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

class Competence(Base):
    __tablename__ = "competences"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

class TestResult(Base):
    __tablename__ = "test_results"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    competence_id = Column(Integer, ForeignKey("competences.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, CheckConstraint('score BETWEEN 200 AND 800'))
    assessment_date = Column(DateTime)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

class Interest(Base):
    __tablename__ = "interests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Integer, default=1)

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    parser_type = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    url = Column(String(500))
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"))
    event_date = Column(DateTime)
    location = Column(String(500))
    city = Column(String(100))
    address = Column(Text)
    format = Column(String(20), default='offline')
    organizer = Column(String(255))
    image_url = Column(String(500))
    price_type = Column(String(50))
    price = Column(String(100))
    status = Column(String(20), default='active')
    
    source = relationship("Source")

class EventCompetence(Base):
    __tablename__ = "event_competences"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    competence_id = Column(Integer, ForeignKey("competences.id", ondelete="CASCADE"), nullable=False)
    relevance = Column(Integer, CheckConstraint('relevance BETWEEN 1 AND 5'))

class EventCategory(Base):
    __tablename__ = "event_categories"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)

class ActionType(Base):
    __tablename__ = "action_types"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

class UserAction(Base):
    __tablename__ = "user_actions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    action_type_id = Column(Integer, ForeignKey("action_types.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, CheckConstraint('rating BETWEEN 1 AND 5'))
    review_text = Column(Text)
    created_at = Column(DateTime, server_default=func.now())