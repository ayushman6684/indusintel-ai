"""
Database models for IndusIntel AI.

Kept intentionally simple for the 5-day MVP timeline (see Section 7 of the spec):
Product, ProductSpecification, Document, ValidationResult.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    product_code = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    quality_score = Column(Float, default=0.0)
    status = Column(String, default="draft")  # draft | processing | completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    specifications = relationship(
        "ProductSpecification", back_populates="product", cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document", back_populates="product", cascade="all, delete-orphan"
    )
    validation_results = relationship(
        "ValidationResult", back_populates="product", cascade="all, delete-orphan"
    )


class ProductSpecification(Base):
    __tablename__ = "product_specifications"

    id = Column(String, primary_key=True, default=gen_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    field_name = Column(String, nullable=False)
    value = Column(String, nullable=True)
    normalized_value = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    status = Column(String, default="UNKNOWN")  # PASS | WARNING | FAIL | UNKNOWN
    source = Column(String, default="UNKNOWN")  # SOURCE_VERIFIED | AI_ENRICHED | USER_PROVIDED | INFERRED | UNKNOWN
    source_page = Column(Integer, nullable=True)

    product = relationship("Product", back_populates="specifications")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    filename = Column(String, nullable=False)
    document_type = Column(String, nullable=True)  # pdf | csv | text | image
    extracted_text = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="documents")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String, primary_key=True, default=gen_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    field_name = Column(String, nullable=False)
    severity = Column(String, default="INFO")  # INFO | WARNING | ERROR
    message = Column(Text, nullable=True)
    status = Column(String, default="PASS")  # PASS | WARNING | FAIL

    product = relationship("Product", back_populates="validation_results")
