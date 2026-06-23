from datetime import datetime
from pydantic import BaseModel


class EnrichmentItemSuggestion(BaseModel):
    itemIndex: int
    originalDescription: str
    suggestedSku: str | None = None
    suggestedUpc: str | None = None
    suggestedDescription: str | None = None
    suggestedListPrice: float | None = None
    suggestedDepartmentCode: int | None = None
    suggestedSubDepartmentCode: int | None = None
    suggestedClassCode: int | None = None
    suggestedSubclassCode: int | None = None
    matchedProductId: int | None = None
    matchType: str | None = None
    confidence: float | None = None
    requiresReview: bool = False


class EnrichmentPreview(BaseModel):
    enrichmentId: int
    ticketId: int
    ocrResultId: int
    status: str
    rawText: str | None = None
    extractedItems: list[dict]
    suggestions: list[EnrichmentItemSuggestion]
    nearbyStoreCodes: list[str] = []


class EnrichmentItemUpdate(BaseModel):
    itemIndex: int
    sku: str | None = None
    upc: str | None = None
    description: str | None = None
    quantity: float | None = None
    unitPrice: float | None = None
    lineAmount: float | None = None
    departmentCode: int | None = None
    subDepartmentCode: int | None = None
    classCode: int | None = None
    subclassCode: int | None = None


class EnrichmentConfirmRequest(BaseModel):
    notes: str | None = None
    items: list[EnrichmentItemUpdate]


class EnrichmentRejectRequest(BaseModel):
    notes: str | None = None
