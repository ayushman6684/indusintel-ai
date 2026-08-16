"""
Pydantic schemas — the strict contracts for API I/O and (from Day 2 onward)
for validating AI JSON output. Never allow the AI to return arbitrary
unstructured output; it must conform to these shapes.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict


# ---------- Product Specification ----------

class SpecificationBase(BaseModel):
    field_name: str
    value: Optional[str] = None
    normalized_value: Optional[str] = None
    unit: Optional[str] = None
    confidence: float = 0.0
    status: str = "UNKNOWN"
    source: str = "UNKNOWN"
    source_page: Optional[int] = None


class SpecificationOut(SpecificationBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: str


# ---------- Validation Result ----------

class ValidationResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    field_name: str
    severity: str
    message: Optional[str] = None
    status: str


# ---------- Document ----------

class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    filename: str
    document_type: Optional[str] = None
    uploaded_at: datetime


# ---------- Product ----------

class ProductCreate(BaseModel):
    name: str
    product_code: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    product_code: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    quality_score: float
    status: str
    created_at: datetime
    updated_at: datetime


class ProductDetailOut(ProductOut):
    specifications: List[SpecificationOut] = []
    documents: List[DocumentOut] = []
    validation_results: List[ValidationResultOut] = []


# ---------- Standardized Product Intelligence Schema (Section 4) ----------
# This is the target schema the AI pipeline (Day 2+) must structure data into.
# Kept here now so the extraction endpoint can already return data compatible
# with it.

class DimensionsSchema(BaseModel):
    length: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None


class ProductIntelligenceSchema(BaseModel):
    product_name: str = ""
    product_code: str = ""
    category: str = ""
    manufacturer: str = ""
    description: str = ""
    material: str = ""
    dimensions: DimensionsSchema = DimensionsSchema()
    weight: str = ""
    voltage: str = ""
    power: str = ""
    temperature_range: str = ""
    pressure_rating: str = ""
    flow_rate: str = ""
    operating_environment: str = ""
    certifications: List[str] = []
    applications: List[str] = []
    features: List[str] = []
    compatibility: List[str] = []
    technical_specifications: Dict[str, Any] = {}
    source_references: List[Dict[str, Any]] = []
    confidence_scores: Dict[str, float] = {}
    validation_status: str = "UNKNOWN"
    missing_fields: List[str] = []


# ---------- Upload / Extraction ----------

class ExtractionResponse(BaseModel):
    document_id: str
    filename: str
    document_type: str
    extracted_text: str
    char_count: int
    page_count: Optional[int] = None
    product_id: Optional[str] = None
