from unittest.mock import patch
import pytest
from app.models.catalog import CompetitorStore, ChedrauiProduct, CompetitorProductMapping, NearbyStore
from app.models.ocr import OcrResult
from app.models.enrichment import TicketEnrichment
from app.services.enrichment_service import run_enrichment, get_enrichment_preview, confirm_enrichment, reject_enrichment


def _seed_ocr(db_session, ticket):
    ocr = OcrResult(
        ocr_id=1,
        ticket_scan_file_id=1,
        raw_text="MOCK OCR",
        extracted_items=[
            {"code": "P01", "description": "LECHE LALA 1L", "quantity": 2, "unitPrice": 25.50, "lineAmount": 51.00},
            {"code": "P02", "description": "PAN BIMBO 680G", "quantity": 1, "unitPrice": 42.00, "lineAmount": 42.00},
        ],
        llm_model="mock",
        confidence=0.95,
    )
    db_session.add(ocr)
    db_session.commit()
    return ocr


def _seed_catalogs(db_session):
    prod = ChedrauiProduct(product_id=1, sku="CHD001", upc="750001", description="LECHE LALA 1L ENTERA", list_price=25.50, department_code=1, sub_department_code=10, class_code=100, subclass_code=1000, is_active=True)
    db_session.add(prod)
    mapping = CompetitorProductMapping(mapping_id=1, business_code="01", competitor_code="P01", competitor_description="LECHE LALA 1L", chedraui_product_id=1, match_type="CODE", confidence=0.98, is_active=True)
    db_session.add(mapping)
    nearby = NearbyStore(nearby_id=1, business_code="01", store_code="0123", nearby_chedraui_store_code="CHD001", distance_km=5.0, is_active=True)
    db_session.add(nearby)
    db_session.commit()


class TestEnrichmentService:
    def test_run_enrichment_auto_complete(self, supervisor_ctx, db_session, seed_ticket_with_scan):
        ticket = seed_ticket_with_scan
        _seed_ocr(db_session, ticket)
        _seed_catalogs(db_session)

        result = run_enrichment(db_session, supervisor_ctx, ticket.ticket_id)
        assert result["status"] == "REVIEW"
        assert len(result["suggestions"]) == 2
        assert result["nearbyStoreCodes"] == ["CHD001"]

        enrichment = db_session.query(TicketEnrichment).filter(TicketEnrichment.ticket_id == ticket.ticket_id).first()
        assert enrichment is not None
        assert enrichment.status == "REVIEW"

    def test_run_enrichment_no_ocr(self, supervisor_ctx, db_session, seed_ticket_with_scan):
        with pytest.raises(ValueError, match="NO_OCR_RESULT"):
            run_enrichment(db_session, supervisor_ctx, seed_ticket_with_scan.ticket_id)

    def test_run_enrichment_forbidden(self, store_user_ctx, db_session, seed_ticket_with_scan):
        ticket = seed_ticket_with_scan
        from app.models.ticket import TicketStore
        db_session.query(TicketStore).filter(TicketStore.ticket_id == ticket.ticket_id).delete()
        db_session.commit()
        db_session.refresh(ticket)
        with pytest.raises(PermissionError):
            run_enrichment(db_session, store_user_ctx, ticket.ticket_id)

    def test_get_enrichment_preview(self, supervisor_ctx, db_session, seed_ticket_with_scan):
        ticket = seed_ticket_with_scan
        _seed_ocr(db_session, ticket)

        preview = get_enrichment_preview(db_session, supervisor_ctx, ticket.ticket_id)
        assert preview is None

        _seed_catalogs(db_session)
        run_enrichment(db_session, supervisor_ctx, ticket.ticket_id)

        preview = get_enrichment_preview(db_session, supervisor_ctx, ticket.ticket_id)
        assert preview is not None
        assert preview["status"] == "REVIEW"
        assert len(preview["extractedItems"]) == 2

    def test_confirm_enrichment(self, supervisor_ctx, db_session, seed_ticket_with_scan):
        ticket = seed_ticket_with_scan
        _seed_ocr(db_session, ticket)
        _seed_catalogs(db_session)
        run_enrichment(db_session, supervisor_ctx, ticket.ticket_id)

        result = confirm_enrichment(db_session, supervisor_ctx, ticket.ticket_id, notes="Approved")
        assert result["status"] == "COMPLETED"

        enrichment = db_session.query(TicketEnrichment).filter(TicketEnrichment.ticket_id == ticket.ticket_id).first()
        assert enrichment.status == "COMPLETED"
        assert enrichment.reviewed_by_user_id == supervisor_ctx.user_id

    def test_reject_enrichment(self, supervisor_ctx, db_session, seed_ticket_with_scan):
        ticket = seed_ticket_with_scan
        _seed_ocr(db_session, ticket)
        _seed_catalogs(db_session)
        run_enrichment(db_session, supervisor_ctx, ticket.ticket_id)

        result = reject_enrichment(db_session, supervisor_ctx, ticket.ticket_id, notes="Rejected")
        assert result["status"] == "REJECTED"

        enrichment = db_session.query(TicketEnrichment).filter(TicketEnrichment.ticket_id == ticket.ticket_id).first()
        assert enrichment.status == "REJECTED"

    def test_confirm_enrichment_with_items(self, supervisor_ctx, db_session, seed_ticket_with_scan):
        ticket = seed_ticket_with_scan
        _seed_ocr(db_session, ticket)
        _seed_catalogs(db_session)
        run_enrichment(db_session, supervisor_ctx, ticket.ticket_id)

        items = [
            {"itemIndex": 0, "sku": "CHD001", "upc": "750001", "description": "LECHE LALA 1L ENTERA EDITED"},
            {"itemIndex": 1, "sku": None, "description": "PAN BIMBO 680G"},
        ]
        result = confirm_enrichment(db_session, supervisor_ctx, ticket.ticket_id, notes="Edited and approved", items=items)
        assert result["status"] == "COMPLETED"
