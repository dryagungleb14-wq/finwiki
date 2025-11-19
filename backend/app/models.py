from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class QAPairStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    unanswered = "unanswered"

class QAPair(Base):
    __tablename__ = "qa_pairs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    question_processed = Column(String, nullable=True)
    answer_processed = Column(String, nullable=True)
    status = Column(Enum(QAPairStatus), default=QAPairStatus.pending, nullable=False)
    submitted_by = Column(String, nullable=True)
    slack_user = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)

    keywords = relationship("Keyword", back_populates="qa_pair", cascade="all, delete-orphan")

class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    qa_pair_id = Column(Integer, ForeignKey("qa_pairs.id"), nullable=False)
    keyword = Column(String, nullable=False)

    qa_pair = relationship("QAPair", back_populates="keywords")

