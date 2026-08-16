"""
Product & document ingestion endpoints.

Day 1 scope: create/list/get products, upload a PDF/CSV/text file (or submit
raw text) and get back the extracted text with a stored Document record.
Structuring (AI), enrichment, and validation endpoints are stubbed to return
empty/placeholder data and will be implemented Day 2-3 per the spec.
"""
from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.services.pdf_extractor import extract_text
from app.services.ai_provider import get_ai_provider, AIProviderError
from app.services.agents import run_extraction_agent, run_structuring_agent, AgentError

router = APIRouter(prefix="/api/products", tags=["products"])


# ---------- CRUD ----------

@router.post("", response_model=schemas.ProductOut)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    product = models.Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("", response_model=List[schemas.ProductOut])
def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Product)
    if category:
        query = query.filter(models.Product.category == category)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (models.Product.name.ilike(like)) | (models.Product.product_code.ilike(like))
        )
    return query.order_by(models.Product.created_at.desc()).all()


@router.get("/{product_id}", response_model=schemas.ProductDetailOut)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ---------- Upload / Extraction (Stage 1: Extract) ----------

@router.post("/upload", response_model=schemas.ExtractionResponse)
async def upload_document(
    file: Optional[UploadFile] = File(None),
    manual_text: Optional[str] = Form(None),
    product_name: Optional[str] = Form(None),
    product_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Accepts either a file upload (PDF/CSV/text) OR raw manual_text, extracts
    the text, stores a Document record, and links/creates a draft Product.
    This satisfies the Day 1 goal:
        Upload PDF -> Backend receives PDF -> Text extracted -> displayed.
    """
    if not file and not manual_text:
        raise HTTPException(status_code=400, detail="Provide a file or manual_text")

    if file:
        file_bytes = await file.read()
        try:
            doc_type, extracted_text, count = extract_text(
                file.filename or "upload", file.content_type, file_bytes
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        filename = file.filename or "upload"
        page_count = count if doc_type == "pdf" else None
    else:
        doc_type = "text"
        extracted_text = manual_text or ""
        filename = "manual_input.txt"
        page_count = None

    # Resolve or create the associated product (draft, to be structured on Day 2)
    product: Optional[models.Product] = None
    if product_id:
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="product_id not found")
    else:
        product = models.Product(
            name=product_name or filename.rsplit(".", 1)[0],
            status="processing",
        )
        db.add(product)
        db.commit()
        db.refresh(product)

    document = models.Document(
        product_id=product.id,
        filename=filename,
        document_type=doc_type,
        extracted_text=extracted_text,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return schemas.ExtractionResponse(
        document_id=document.id,
        filename=filename,
        document_type=doc_type,
        extracted_text=extracted_text,
        char_count=len(extracted_text),
        page_count=page_count,
        product_id=product.id,
    )


# ---------- Specifications / Validation (stubs, built out Day 2-3) ----------

@router.get("/{product_id}/specifications", response_model=List[schemas.SpecificationOut])
def get_specifications(product_id: str, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.specifications


@router.get("/{product_id}/validation", response_model=List[schemas.ValidationResultOut])
def get_validation(product_id: str, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.validation_results


@router.post("/{product_id}/process", response_model=schemas.ProductDetailOut)
def process_product(product_id: str, db: Session = Depends(get_db)):
    """
    Runs Stage 1b (Extraction Agent) + Stages 2-3 (Structuring Agent) over
    every document attached to this product, then persists the result as
    ProductSpecification rows and updates the Product's top-level fields.

    Enrichment and Validation (Stages 4-5) are Day 3 — specifications are
    stored here with status="UNKNOWN" until the Validation Agent runs.
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not product.documents:
        raise HTTPException(
            status_code=422,
            detail="This product has no uploaded documents to process. Upload a datasheet first.",
        )

    combined_text = "\n\n---\n\n".join(
        d.extracted_text for d in product.documents if d.extracted_text
    )
    if not combined_text.strip():
        raise HTTPException(status_code=422, detail="No extractable text found in this product's documents.")

    try:
        ai = get_ai_provider()
        facts = run_extraction_agent(ai, combined_text)
        structured = run_structuring_agent(ai, facts, category_hint=product.category)
    except (AgentError, AIProviderError) as e:
        raise HTTPException(status_code=502, detail=str(e))

    _persist_structured_product(db, product, structured)

    db.commit()
    db.refresh(product)
    return product


def _persist_structured_product(
    db: Session, product: models.Product, structured: schemas.ProductIntelligenceSchema
) -> None:
    """Flatten a ProductIntelligenceSchema into ProductSpecification rows
    and update the parent Product's summary fields. Replaces any existing
    specifications for this product (re-processing overwrites, it doesn't
    duplicate)."""

    # Update top-level product fields (only overwrite with non-empty values
    # so a manually-entered product name isn't clobbered by a blank result).
    if structured.product_name:
        product.name = structured.product_name
    if structured.product_code:
        product.product_code = structured.product_code
    if structured.category:
        product.category = structured.category
    if structured.manufacturer:
        product.manufacturer = structured.manufacturer
    if structured.description:
        product.description = structured.description
    product.status = "completed"

    # Temporary quality signal until the full weighted IndusIntel Data
    # Quality Score (completeness/validation/source/normalization/
    # traceability) lands on Day 3 — average field confidence is a
    # reasonable proxy in the meantime.
    if structured.confidence_scores:
        product.quality_score = round(
            sum(structured.confidence_scores.values()) / len(structured.confidence_scores), 1
        )

    # Clear old specs before writing the new set.
    db.query(models.ProductSpecification).filter(
        models.ProductSpecification.product_id == product.id
    ).delete()

    source_page_by_field = {
        ref.get("field"): ref.get("page")
        for ref in structured.source_references
        if isinstance(ref, dict) and ref.get("field")
    }

    def add_spec(field_name: str, value, unit: str | None = None):
        if value in (None, "", [], {}):
            return
        value_str = value if isinstance(value, str) else str(value)
        confidence = structured.confidence_scores.get(field_name, 0)
        source = "AI_ENRICHED" if field_name in structured.missing_fields else "SOURCE_VERIFIED"
        db.add(
            models.ProductSpecification(
                product_id=product.id,
                field_name=field_name,
                value=value_str,
                normalized_value=value_str,
                unit=unit,
                confidence=float(confidence) if confidence else 0.0,
                status="UNKNOWN",  # set by the Validation Agent, Day 3
                source=source,
                source_page=source_page_by_field.get(field_name),
            )
        )

    add_spec("material", structured.material)
    add_spec("weight", structured.weight)
    add_spec("voltage", structured.voltage)
    add_spec("power", structured.power)
    add_spec("temperature_range", structured.temperature_range)
    add_spec("pressure_rating", structured.pressure_rating)
    add_spec("flow_rate", structured.flow_rate)
    add_spec("operating_environment", structured.operating_environment)

    if structured.dimensions.length:
        add_spec("dimensions_length", structured.dimensions.length)
    if structured.dimensions.width:
        add_spec("dimensions_width", structured.dimensions.width)
    if structured.dimensions.height:
        add_spec("dimensions_height", structured.dimensions.height)

    for key, value in structured.technical_specifications.items():
        add_spec(key, value)

    if structured.certifications:
        add_spec("certifications", ", ".join(structured.certifications))
    if structured.applications:
        add_spec("applications", ", ".join(structured.applications))
    if structured.features:
        add_spec("features", ", ".join(structured.features))
    if structured.compatibility:
        add_spec("compatibility", ", ".join(structured.compatibility))


@router.post("/{product_id}/enrich")
def enrich_product(product_id: str):
    raise HTTPException(status_code=501, detail="Enrichment agent arrives Day 3.")


@router.post("/{product_id}/validate")
def validate_product(product_id: str):
    raise HTTPException(status_code=501, detail="Validation agent arrives Day 3.")


@router.get("/{product_id}/export/json")
def export_json(product_id: str):
    raise HTTPException(status_code=501, detail="Export implemented Day 4.")


@router.get("/{product_id}/export/csv")
def export_csv(product_id: str):
    raise HTTPException(status_code=501, detail="Export implemented Day 4.")


# ---------- Dashboard summary ----------

@router.get("/dashboard/summary", tags=["dashboard"])
def dashboard_summary(db: Session = Depends(get_db)):
    total_products = db.query(func.count(models.Product.id)).scalar() or 0
    processed = (
        db.query(func.count(models.Product.id))
        .filter(models.Product.status == "completed")
        .scalar()
        or 0
    )
    avg_quality = db.query(func.avg(models.Product.quality_score)).scalar() or 0
    validation_issues = (
        db.query(func.count(models.ValidationResult.id))
        .filter(models.ValidationResult.status != "PASS")
        .scalar()
        or 0
    )
    recent = (
        db.query(models.Product)
        .order_by(models.Product.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_products": total_products,
        "products_processed": processed,
        "average_quality": round(float(avg_quality), 1),
        "validation_issues": validation_issues,
        "recent_products": [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "status": p.status,
                "quality_score": p.quality_score,
            }
            for p in recent
        ],
    }
