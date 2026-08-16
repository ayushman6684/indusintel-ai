"""
AI Pipeline agents — Section 9 of the spec: separate, single-purpose
prompts rather than one giant system prompt.

Day 2 implements two agents:

- ExtractionAgent: pulls out only the facts explicitly present in the raw
  text (no guessing, no filling gaps), preserving page references.
- StructuringAgent: takes those facts and converts them into the
  standardized, category-aware ProductIntelligenceSchema, strictly
  validated with Pydantic. The AI is never trusted to return arbitrary
  unstructured output — every response is parsed through the schema, and a
  bad response raises rather than silently producing garbage.

Enrichment, Validation, and Explanation agents are Day 3 work.
"""
from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.schemas import ProductIntelligenceSchema
from app.services.ai_provider import AIProvider, AIProviderError
from app.services.normalize import normalize_category, normalize_field_name, normalize_value
from app.services.schema_registry import CATEGORIES, expected_fields_for_category


class AgentError(Exception):
    """Raised when an agent cannot produce a valid, schema-conformant result."""


EXTRACTION_SYSTEM_PROMPT = """You are the Extraction Agent for an industrial product intelligence system.

Your ONLY job is to extract facts that are EXPLICITLY present in the provided document text. You do not infer, guess, or add information that isn't directly stated. If the document doesn't mention something, do not include it.

The text may contain [PAGE N] markers showing which page each section came from — preserve these as page references for whatever facts you extract from that section.

Return a JSON object with this shape:
{
  "facts": [
    {"field": "<short field name>", "value": "<exact value as stated>", "page": <page number or null>, "quote": "<short exact quote from the source, max 15 words>"}
  ]
}

Extract facts for things like: product name, product code, manufacturer, category, description, material, dimensions, weight, voltage, power, temperature range, pressure rating, flow rate, operating environment, certifications, applications, features, compatibility, and any other technical specification explicitly stated. Do not fabricate a field's presence if it isn't in the text."""


STRUCTURING_SYSTEM_PROMPT_TEMPLATE = """You are the Structuring Agent for an industrial product intelligence system.

Convert the extracted facts below into a standardized product schema. Use ONLY the facts provided — do not add information that wasn't extracted. If a field has no corresponding fact, leave it as an empty string, empty list, or empty object as appropriate.

Known product categories: {categories}. Pick the closest match for "category", or "Other" if none fit.

Return a JSON object matching EXACTLY this shape (all keys required, use empty values for anything not present in the facts):
{{
  "product_name": "",
  "product_code": "",
  "category": "",
  "manufacturer": "",
  "description": "",
  "material": "",
  "dimensions": {{"length": "", "width": "", "height": ""}},
  "weight": "",
  "voltage": "",
  "power": "",
  "temperature_range": "",
  "pressure_rating": "",
  "flow_rate": "",
  "operating_environment": "",
  "certifications": [],
  "applications": [],
  "features": [],
  "compatibility": [],
  "technical_specifications": {{}},
  "source_references": [{{"field": "", "value": "", "page": null}}],
  "confidence_scores": {{}},
  "validation_status": "UNKNOWN",
  "missing_fields": []
}}

For "technical_specifications", put any category-specific fields that don't have a dedicated top-level key (for this category, look especially for: {category_fields}).

For "confidence_scores", give every populated field a score 0-100 based on how explicitly and unambiguously it was stated in the source facts (explicit numeric values with units = high confidence like 90-99; vague or partially-stated values = medium 70-89; anything you're not fully sure about = low, under 70).

For "missing_fields", list the names of important fields (from the schema above) that had no corresponding fact at all.

For "source_references", include one entry per populated field showing which page (if any) it came from."""


def run_extraction_agent(ai: AIProvider, raw_text: str) -> list[dict[str, Any]]:
    """Stage 1b: pull explicit facts + page refs out of raw extracted text."""
    if not raw_text or not raw_text.strip():
        raise AgentError("No text to extract from.")

    try:
        result = ai.complete_json(
            EXTRACTION_SYSTEM_PROMPT,
            f"Document text:\n\n{raw_text[:12000]}",
            max_tokens=2500,
        )
    except AIProviderError as e:
        raise AgentError(f"Extraction agent failed: {e}") from e

    facts = result.get("facts", [])
    if not isinstance(facts, list):
        raise AgentError("Extraction agent returned an unexpected shape (facts is not a list).")
    return facts


def run_structuring_agent(
    ai: AIProvider, facts: list[dict[str, Any]], category_hint: str | None = None
) -> ProductIntelligenceSchema:
    """Stage 2+3: normalize and structure facts into ProductIntelligenceSchema."""
    if not facts:
        raise AgentError("No facts to structure.")

    system_prompt = STRUCTURING_SYSTEM_PROMPT_TEMPLATE.format(
        categories=", ".join(CATEGORIES),
        category_fields=", ".join(expected_fields_for_category(category_hint or "")) or "none known yet",
    )

    user_prompt = f"Extracted facts (JSON):\n\n{facts}"
    if category_hint:
        user_prompt += f"\n\nHint: this product is likely in the '{category_hint}' category."

    try:
        result = ai.complete_json(system_prompt, user_prompt, max_tokens=3000)
    except AIProviderError as e:
        raise AgentError(f"Structuring agent failed: {e}") from e

    # Deterministic normalization pass (Stage 2) before schema validation —
    # never let the LLM's formatting choices decide what "10 bar" vs
    # "10Bar" means.
    result["category"] = normalize_category(result.get("category"), CATEGORIES)

    for unit_field in ("pressure_rating", "flow_rate", "weight", "voltage", "power"):
        if result.get(unit_field):
            normalized, _unit = normalize_value(result[unit_field])
            if normalized:
                result[unit_field] = normalized

    tech_specs = result.get("technical_specifications") or {}
    if isinstance(tech_specs, dict):
        normalized_specs = {}
        for key, value in tech_specs.items():
            norm_key = normalize_field_name(key)
            norm_value, _unit = normalize_value(value) if isinstance(value, str) else (value, None)
            normalized_specs[norm_key] = norm_value if norm_value is not None else value
        result["technical_specifications"] = normalized_specs

    try:
        return ProductIntelligenceSchema.model_validate(result)
    except ValidationError as e:
        raise AgentError(f"Structuring agent output failed schema validation: {e}") from e
