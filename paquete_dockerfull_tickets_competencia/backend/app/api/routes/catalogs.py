from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.security.auth import get_current_context
from app.schemas.security import SecurityContext
from app.schemas.common import ApiResponse
from app.schemas.catalog import CompetitorStoreDTO, ChedrauiProductDTO, CompetitorProductMappingDTO, NearbyStoreDTO
from app.services.catalog_service import CatalogService
from app.services.security_service import require_admin

router = APIRouter(prefix="/api/v1/catalogs", tags=["catalogs"])


def _get_svc(db: Session = Depends(get_db)) -> CatalogService:
    return CatalogService(db)


def _check_admin(ctx: SecurityContext):
    try:
        require_admin(ctx)
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")


# ── CSV Import / Template (must be before {id} routes) ──────────

CATALOG_NAMES = {"competitor-stores", "chedraui-products", "competitor-mappings", "nearby-stores"}


@router.get("/{catalog}/template")
def download_template(catalog: str, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    if catalog not in CATALOG_NAMES:
        raise HTTPException(status_code=404, detail="UNKNOWN_CATALOG")
    csv_content = svc.get_template_csv(catalog)
    if csv_content is None:
        raise HTTPException(status_code=404, detail="UNKNOWN_CATALOG")
    return PlainTextResponse(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{catalog}.csv"'})


@router.post("/{catalog}/import")
def import_catalog_csv(catalog: str, file: UploadFile = File(...), svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    if catalog not in CATALOG_NAMES:
        raise HTTPException(status_code=404, detail="UNKNOWN_CATALOG")
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="INVALID_FILE_TYPE")

    try:
        content = file.file.read().decode("utf-8-sig")
    except Exception:
        raise HTTPException(status_code=400, detail="INVALID_FILE_ENCODING")

    try:
        result = svc.import_csv(catalog, content)
        return ApiResponse.ok(result)
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


# ── CompetitorStore ─────────────────────────────────────────

@router.get("/competitor-stores")
def list_competitor_stores(svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    return ApiResponse.ok(svc.list_competitor_stores())


@router.get("/competitor-stores/{store_id}")
def get_competitor_store(store_id: int, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    r = svc.get_competitor_store(store_id)
    if not r:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return ApiResponse.ok(r)


@router.post("/competitor-stores")
def create_competitor_store(body: CompetitorStoreDTO, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    return ApiResponse.ok(svc.create_competitor_store(body.model_dump(exclude_unset=True, exclude={'storeId'})))


@router.put("/competitor-stores/{store_id}")
def update_competitor_store(store_id: int, body: CompetitorStoreDTO, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    r = svc.update_competitor_store(store_id, body.model_dump(exclude_unset=True, exclude={'storeId'}))
    if not r:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return ApiResponse.ok(r)


@router.delete("/competitor-stores/{store_id}")
def delete_competitor_store(store_id: int, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    if not svc.delete_competitor_store(store_id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return ApiResponse.ok({"message": "Deleted"})


# ── ChedrauiProduct ─────────────────────────────────────────

@router.get("/chedraui-products")
def list_chedraui_products(svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    return ApiResponse.ok(svc.list_chedraui_products())


@router.get("/chedraui-products/{product_id}")
def get_chedraui_product(product_id: int, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    r = svc.get_chedraui_product(product_id)
    if not r:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return ApiResponse.ok(r)


@router.post("/chedraui-products")
def create_chedraui_product(body: ChedrauiProductDTO, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    return ApiResponse.ok(svc.create_chedraui_product(body.model_dump(exclude_unset=True, exclude={'productId'})))


@router.put("/chedraui-products/{product_id}")
def update_chedraui_product(product_id: int, body: ChedrauiProductDTO, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    r = svc.update_chedraui_product(product_id, body.model_dump(exclude_unset=True, exclude={'productId'}))
    if not r:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return ApiResponse.ok(r)


@router.delete("/chedraui-products/{product_id}")
def delete_chedraui_product(product_id: int, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    if not svc.delete_chedraui_product(product_id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return ApiResponse.ok({"message": "Deleted"})


# ── CompetitorProductMapping ────────────────────────────────

@router.get("/competitor-mappings")
def list_mappings(svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    return ApiResponse.ok(svc.list_mappings())


@router.get("/competitor-mappings/{mapping_id}")
def get_mapping(mapping_id: int, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    r = svc.get_mapping(mapping_id)
    if not r:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return ApiResponse.ok(r)


@router.post("/competitor-mappings")
def create_mapping(body: CompetitorProductMappingDTO, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    return ApiResponse.ok(svc.create_mapping(body.model_dump(exclude_unset=True, exclude={'mappingId'})))


@router.put("/competitor-mappings/{mapping_id}")
def update_mapping(mapping_id: int, body: CompetitorProductMappingDTO, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    r = svc.update_mapping(mapping_id, body.model_dump(exclude_unset=True, exclude={'mappingId'}))
    if not r:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return ApiResponse.ok(r)


@router.delete("/competitor-mappings/{mapping_id}")
def delete_mapping(mapping_id: int, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    if not svc.delete_mapping(mapping_id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return ApiResponse.ok({"message": "Deleted"})


# ── NearbyStore ─────────────────────────────────────────────

@router.get("/nearby-stores")
def list_nearby_stores(svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    return ApiResponse.ok(svc.list_nearby_stores())


@router.get("/nearby-stores/{nearby_id}")
def get_nearby_store(nearby_id: int, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    r = svc.get_nearby_store(nearby_id)
    if not r:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return ApiResponse.ok(r)


@router.post("/nearby-stores")
def create_nearby_store(body: NearbyStoreDTO, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    return ApiResponse.ok(svc.create_nearby_store(body.model_dump(exclude_unset=True, exclude={'nearbyId'})))


@router.put("/nearby-stores/{nearby_id}")
def update_nearby_store(nearby_id: int, body: NearbyStoreDTO, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    r = svc.update_nearby_store(nearby_id, body.model_dump(exclude_unset=True, exclude={'nearbyId'}))
    if not r:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return ApiResponse.ok(r)


@router.delete("/nearby-stores/{nearby_id}")
def delete_nearby_store(nearby_id: int, svc: CatalogService = Depends(_get_svc), ctx: SecurityContext = Depends(get_current_context)):
    _check_admin(ctx)
    if not svc.delete_nearby_store(nearby_id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return ApiResponse.ok({"message": "Deleted"})
