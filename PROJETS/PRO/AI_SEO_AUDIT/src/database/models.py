"""SQLAlchemy database models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .session import Base


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    company_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_audit_at = Column(DateTime)

    # Relationships
    audits = relationship("Audit", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Audit(Base):
    """Audit model."""
    __tablename__ = "audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    sector = Column(String(100), nullable=False, index=True)
    location = Column(String(255))
    language = Column(String(5), default="fr", nullable=False)
    plan = Column(String(20), nullable=False, index=True)  # freemium/starter/pro
    visibility_score = Column(Float)
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending/running/completed/failed
    results = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="audits")
    queries = relationship("Query", back_populates="audit", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="audit", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="audit", uselist=False)

    # Indexes
    __table_args__ = (
        Index('ix_audits_status_created_at', 'status', 'created_at'),
    )

    def __repr__(self):
        return f"<Audit {self.company_name} - {self.status}>"


class Query(Base):
    """Query model - individual queries tested during audit."""
    __tablename__ = "queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_id = Column(UUID(as_uuid=True), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    ai_provider = Column(String(50), nullable=False)  # chatgpt/claude/gemini/perplexity
    ai_response = Column(Text)
    company_mentioned = Column(Boolean, default=False)
    position = Column(Integer)  # Position if mentioned (1-N)
    competitors_found = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    audit = relationship("Audit", back_populates="queries")

    def __repr__(self):
        return f"<Query {self.query_text[:50]}... - {self.ai_provider}>"


class Recommendation(Base):
    """Recommendation model - optimization recommendations."""
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_id = Column(UUID(as_uuid=True), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # content/structured_data/editorial
    priority = Column(Integer, default=5)  # 1-5 (1 = urgent)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    content = Column(JSONB, default=dict)
    integration_guide = Column(Text)
    estimated_impact = Column(String(20))  # low/medium/high
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    audit = relationship("Audit", back_populates="recommendations")

    def __repr__(self):
        return f"<Recommendation {self.title} - P{self.priority}>"


class Payment(Base):
    """Payment model - Stripe payments."""
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    audit_id = Column(UUID(as_uuid=True), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True)
    stripe_checkout_id = Column(String(255), unique=True, nullable=True, index=True)
    plan = Column(String(20), nullable=False)  # starter/pro
    amount = Column(Integer, nullable=False)  # Amount in cents
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending/completed/failed/refunded
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="payments")
    audit = relationship("Audit", back_populates="payment")

    def __repr__(self):
        return f"<Payment {self.plan} - {self.amount/100}€ - {self.status}>"
