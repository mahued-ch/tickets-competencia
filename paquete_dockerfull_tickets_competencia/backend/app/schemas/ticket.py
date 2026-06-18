from datetime import date, datetime
from pydantic import BaseModel


class TicketSummaryDTO(BaseModel):
    ticketId: int
    sourceTicketCode: str
    sourceBusinessCode: str
    sourceStoreCode: str
    sourceTicketDate: date
    sourceTicketKey: str
    sourceStatusCode: str | None = None
    scanStatus: str
    hasScanFile: bool
    createdAt: datetime | None = None
    updatedAt: datetime | None = None


class TicketItemDTO(BaseModel):
    ticketItemId: int
    ticketId: int
    itemSequence: int
    productCode: str | None = None
    productDescription: str | None = None
    quantity: float | None = None
    unitPrice: float | None = None
    lineAmount: float | None = None


class TicketStoreDTO(BaseModel):
    ticketStoreId: int
    ticketId: int
    storeCode: str


class ScanFileDTO(BaseModel):
    ticketScanFileId: int
    ticketId: int
    fileName: str
    fileExtension: str
    mimeType: str
    fileSizeBytes: int
    fileHash: str
    storagePath: str
    storageProvider: str
    versionNumber: int
    isActive: bool
    isConfirmed: bool
    uploadedByUserId: int
    uploadedAt: datetime | None = None
    confirmedByUserId: int | None = None
    confirmedAt: datetime | None = None
    notes: str | None = None
