import csv
import io
from sqlalchemy.orm import Session
from app.models.catalog import CompetitorStore, ChedrauiProduct, CompetitorProductMapping, NearbyStore


class CatalogService:
    def __init__(self, db: Session):
        self.db = db

    # ── CompetitorStore ─────────────────────────────────────

    def list_competitor_stores(self) -> list[dict]:
        rows = self.db.query(CompetitorStore).order_by(CompetitorStore.business_code, CompetitorStore.store_code).all()
        return [self._cs_to_dto(r) for r in rows]

    def get_competitor_store(self, store_id: int) -> dict | None:
        r = self.db.query(CompetitorStore).filter(CompetitorStore.store_id == store_id).first()
        return self._cs_to_dto(r) if r else None

    def create_competitor_store(self, data: dict) -> dict:
        r = CompetitorStore(**data)
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return self._cs_to_dto(r)

    def update_competitor_store(self, store_id: int, data: dict) -> dict | None:
        r = self.db.query(CompetitorStore).filter(CompetitorStore.store_id == store_id).first()
        if not r:
            return None
        for k, v in data.items():
            setattr(r, k, v)
        self.db.commit()
        self.db.refresh(r)
        return self._cs_to_dto(r)

    def delete_competitor_store(self, store_id: int) -> bool:
        r = self.db.query(CompetitorStore).filter(CompetitorStore.store_id == store_id).first()
        if not r:
            return False
        self.db.delete(r)
        self.db.commit()
        return True

    @staticmethod
    def _cs_to_dto(r: CompetitorStore) -> dict:
        return {
            "storeId": r.store_id, "businessCode": r.business_code, "storeCode": r.store_code,
            "storeName": r.store_name, "address": r.address, "isActive": r.is_active,
        }

    # ── ChedrauiProduct ─────────────────────────────────────

    def list_chedraui_products(self) -> list[dict]:
        rows = self.db.query(ChedrauiProduct).order_by(ChedrauiProduct.sku).all()
        return [self._cp_to_dto(r) for r in rows]

    def get_chedraui_product(self, product_id: int) -> dict | None:
        r = self.db.query(ChedrauiProduct).filter(ChedrauiProduct.product_id == product_id).first()
        return self._cp_to_dto(r) if r else None

    def create_chedraui_product(self, data: dict) -> dict:
        r = ChedrauiProduct(**data)
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return self._cp_to_dto(r)

    def update_chedraui_product(self, product_id: int, data: dict) -> dict | None:
        r = self.db.query(ChedrauiProduct).filter(ChedrauiProduct.product_id == product_id).first()
        if not r:
            return None
        for k, v in data.items():
            setattr(r, k, v)
        self.db.commit()
        self.db.refresh(r)
        return self._cp_to_dto(r)

    def delete_chedraui_product(self, product_id: int) -> bool:
        r = self.db.query(ChedrauiProduct).filter(ChedrauiProduct.product_id == product_id).first()
        if not r:
            return False
        self.db.delete(r)
        self.db.commit()
        return True

    @staticmethod
    def _cp_to_dto(r: ChedrauiProduct) -> dict:
        return {
            "productId": r.product_id, "sku": r.sku, "upc": r.upc,
            "description": r.description, "listPrice": float(r.list_price) if r.list_price is not None else None,
            "departmentCode": r.department_code, "subDepartmentCode": r.sub_department_code,
            "classCode": r.class_code, "subclassCode": r.subclass_code, "isActive": r.is_active,
        }

    # ── CompetitorProductMapping ────────────────────────────

    def list_mappings(self) -> list[dict]:
        rows = self.db.query(CompetitorProductMapping).order_by(CompetitorProductMapping.business_code).all()
        return [self._cpm_to_dto(r) for r in rows]

    def get_mapping(self, mapping_id: int) -> dict | None:
        r = self.db.query(CompetitorProductMapping).filter(CompetitorProductMapping.mapping_id == mapping_id).first()
        return self._cpm_to_dto(r) if r else None

    def create_mapping(self, data: dict) -> dict:
        r = CompetitorProductMapping(**data)
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return self._cpm_to_dto(r)

    def update_mapping(self, mapping_id: int, data: dict) -> dict | None:
        r = self.db.query(CompetitorProductMapping).filter(CompetitorProductMapping.mapping_id == mapping_id).first()
        if not r:
            return None
        for k, v in data.items():
            setattr(r, k, v)
        self.db.commit()
        self.db.refresh(r)
        return self._cpm_to_dto(r)

    def delete_mapping(self, mapping_id: int) -> bool:
        r = self.db.query(CompetitorProductMapping).filter(CompetitorProductMapping.mapping_id == mapping_id).first()
        if not r:
            return False
        self.db.delete(r)
        self.db.commit()
        return True

    @staticmethod
    def _cpm_to_dto(r: CompetitorProductMapping) -> dict:
        return {
            "mappingId": r.mapping_id, "businessCode": r.business_code,
            "competitorCode": r.competitor_code, "competitorDescription": r.competitor_description,
            "chedrauiProductId": r.chedraui_product_id, "matchType": r.match_type,
            "confidence": float(r.confidence) if r.confidence is not None else None,
            "isActive": r.is_active,
        }

    # ── NearbyStore ─────────────────────────────────────────

    def list_nearby_stores(self) -> list[dict]:
        rows = self.db.query(NearbyStore).order_by(NearbyStore.business_code, NearbyStore.store_code).all()
        return [self._ns_to_dto(r) for r in rows]

    def get_nearby_store(self, nearby_id: int) -> dict | None:
        r = self.db.query(NearbyStore).filter(NearbyStore.nearby_id == nearby_id).first()
        return self._ns_to_dto(r) if r else None

    def create_nearby_store(self, data: dict) -> dict:
        r = NearbyStore(**data)
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return self._ns_to_dto(r)

    def update_nearby_store(self, nearby_id: int, data: dict) -> dict | None:
        r = self.db.query(NearbyStore).filter(NearbyStore.nearby_id == nearby_id).first()
        if not r:
            return None
        for k, v in data.items():
            setattr(r, k, v)
        self.db.commit()
        self.db.refresh(r)
        return self._ns_to_dto(r)

    def delete_nearby_store(self, nearby_id: int) -> bool:
        r = self.db.query(NearbyStore).filter(NearbyStore.nearby_id == nearby_id).first()
        if not r:
            return False
        self.db.delete(r)
        self.db.commit()
        return True

    @staticmethod
    def _ns_to_dto(r: NearbyStore) -> dict:
        return {
            "nearbyId": r.nearby_id, "businessCode": r.business_code, "storeCode": r.store_code,
            "nearbyChedrauiStoreCode": r.nearby_chedraui_store_code,
            "distanceKm": float(r.distance_km) if r.distance_km is not None else None,
            "isActive": r.is_active,
        }

    # ── CSV Templates ──────────────────────────────────────────

    TEMPLATES = {
        "competitor-stores": {
            "headers": ["business_code", "store_code", "store_name", "address", "is_active"],
            "example": ["WMT", "1234", "Walmart Supercenter Ejemplo", "Av. Principal 123", "true"],
        },
        "chedraui-products": {
            "headers": ["sku", "upc", "description", "list_price", "department_code", "sub_department_code", "class_code", "subclass_code", "is_active"],
            "example": ["CHD123", "7501234567890", "Producto Ejemplo", "99.99", "1", "10", "100", "1000", "true"],
        },
        "competitor-mappings": {
            "headers": ["business_code", "competitor_code", "competitor_description", "chedraui_product_id", "match_type", "confidence", "is_active"],
            "example": ["WMT", "PROD001", "Producto Competencia", "1", "MANUAL", "0.95", "true"],
        },
        "nearby-stores": {
            "headers": ["business_code", "store_code", "nearby_chedraui_store_code", "distance_km", "is_active"],
            "example": ["WMT", "1234", "CHD001", "5.5", "true"],
        },
    }

    def get_template_csv(self, catalog: str) -> str | None:
        tpl = self.TEMPLATES.get(catalog)
        if not tpl:
            return None
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(tpl["headers"])
        w.writerow(tpl["example"])
        return out.getvalue()

    def import_csv(self, catalog: str, content: str) -> dict:
        tpl = self.TEMPLATES.get(catalog)
        if not tpl:
            raise ValueError(f"UNKNOWN_CATALOG: {catalog}")

        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            raise ValueError("EMPTY_CSV")

        col_map = {h.lower(): h for h in tpl["headers"]}
        unknown = [c for c in reader.fieldnames if c.lower() not in col_map]
        if unknown:
            raise ValueError(f"UNKNOWN_COLUMNS: {', '.join(unknown)}")

        create_map = {
            "competitor-stores": self.create_competitor_store,
            "chedraui-products": self.create_chedraui_product,
            "competitor-mappings": self.create_mapping,
            "nearby-stores": self.create_nearby_store,
        }
        creator = create_map.get(catalog)
        if not creator:
            raise ValueError(f"UNKNOWN_CATALOG: {catalog}")

        imported = 0
        errors = []

        for row_idx, row in enumerate(reader, start=2):
            try:
                row_lower = {k.lower(): v for k, v in row.items()}
                data = {}
                for header in tpl["headers"]:
                    raw = row_lower.get(header, "")
                    data[header] = raw if raw != "" else None

                # coerce types
                for k in ("list_price", "distance_km", "confidence"):
                    if k in data and data[k] is not None:
                        try:
                            data[k] = float(data[k])
                        except (ValueError, TypeError):
                            data[k] = None
                for k in ("department_code", "sub_department_code", "class_code", "subclass_code", "chedraui_product_id"):
                    if k in data and data[k] is not None:
                        try:
                            data[k] = int(data[k])
                        except (ValueError, TypeError):
                            data[k] = None
                for k in ("is_active",):
                    if k in data and data[k] is not None:
                        if isinstance(data[k], str):
                            data[k] = data[k].strip().lower() in ("true", "1", "yes", "si", "sí")
                for k in ("quantity", "unit_price", "line_amount"):
                    if k in data and data[k] is not None:
                        try:
                            data[k] = float(data[k])
                        except (ValueError, TypeError):
                            data[k] = None

                creator(data)
                imported += 1
            except Exception as ex:
                errors.append({"row": row_idx, "error": str(ex)})

        return {"imported": imported, "errors": errors, "totalRows": row_idx if 'row_idx' in dir() else 0}
