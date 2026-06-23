from pydantic import BaseModel


class CompetitorStoreDTO(BaseModel):
    storeId: int | None = None
    businessCode: str
    storeCode: str
    storeName: str | None = None
    address: str | None = None
    isActive: bool = True


class ChedrauiProductDTO(BaseModel):
    productId: int | None = None
    sku: str
    upc: str | None = None
    description: str | None = None
    listPrice: float | None = None
    departmentCode: int | None = None
    subDepartmentCode: int | None = None
    classCode: int | None = None
    subclassCode: int | None = None
    isActive: bool = True


class CompetitorProductMappingDTO(BaseModel):
    mappingId: int | None = None
    businessCode: str
    competitorCode: str | None = None
    competitorDescription: str | None = None
    chedrauiProductId: int | None = None
    matchType: str | None = None
    confidence: float | None = None
    isActive: bool = True


class NearbyStoreDTO(BaseModel):
    nearbyId: int | None = None
    businessCode: str
    storeCode: str
    nearbyChedrauiStoreCode: str
    distanceKm: float | None = None
    isActive: bool = True
