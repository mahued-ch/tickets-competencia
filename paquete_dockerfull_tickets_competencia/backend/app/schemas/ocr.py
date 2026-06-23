from datetime import datetime
from pydantic import BaseModel


class OcrResultDTO(BaseModel):
    ocrId: int
    ticketScanFileId: int
    rawText: str | None = None
    extractedItems: list[dict] | None = None
    llmModel: str | None = None
    confidence: float | None = None
    createdAt: datetime | None = None


class OcrTriggerResponse(BaseModel):
    ocrId: int
    ticketScanFileId: int
    llmModel: str | None = None
    confidence: float | None = None
    itemCount: int = 0
