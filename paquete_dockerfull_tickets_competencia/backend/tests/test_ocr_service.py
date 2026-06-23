from unittest.mock import patch
import pytest
from app.services.ocr_service import trigger_ocr, get_ocr_result
from app.models.ticket import TicketScanFile
from app.models.ocr import OcrResult


class TestOcrService:
    @patch("app.services.ocr_service._run_tesseract", return_value="MOCK OCR TEXT")
    @patch("app.services.ocr_service._call_llm", return_value=('[{"code":"P01","description":"Item 1","quantity":2,"unitPrice":10,"lineAmount":20}]', 0.95))
    def test_trigger_ocr_success(self, mock_llm, mock_tesseract, supervisor_ctx, db_session, seed_ticket_with_scan):
        ticket = seed_ticket_with_scan
        result = trigger_ocr(db_session, supervisor_ctx, ticket.ticket_id)
        assert result["ocrId"] is not None
        assert result["itemCount"] == 1
        assert result["confidence"] == 0.95

        ocr = db_session.query(OcrResult).filter(OcrResult.ocr_id == result["ocrId"]).first()
        assert ocr is not None
        assert ocr.raw_text == "MOCK OCR TEXT"
        assert ocr.extracted_items is not None

    @patch("app.services.ocr_service._run_tesseract", return_value="")
    @patch("app.services.ocr_service._call_llm", return_value=("[]", 0.0))
    def test_trigger_ocr_empty_result(self, mock_llm, mock_tesseract, supervisor_ctx, db_session, seed_ticket_with_scan):
        ticket = seed_ticket_with_scan
        result = trigger_ocr(db_session, supervisor_ctx, ticket.ticket_id)
        assert result["itemCount"] == 0

    def test_trigger_ocr_no_scan_file(self, supervisor_ctx, db_session, seed_ticket):
        with pytest.raises(ValueError, match="NO_ACTIVE_SCAN_FILE"):
            trigger_ocr(db_session, supervisor_ctx, seed_ticket.ticket_id)

    def test_trigger_ocr_forbidden(self, store_user_ctx, db_session, seed_ticket_with_scan):
        ticket = seed_ticket_with_scan
        from app.models.ticket import TicketStore
        db_session.query(TicketStore).filter(TicketStore.ticket_id == ticket.ticket_id).delete()
        db_session.commit()
        db_session.refresh(ticket)
        with pytest.raises(PermissionError):
            trigger_ocr(db_session, store_user_ctx, ticket.ticket_id)

    @patch("app.services.ocr_service._run_tesseract", return_value="MOCK")
    @patch("app.services.ocr_service._call_llm", return_value=('[{"code":"P01","description":"Item 1"}]', 0.9))
    def test_get_ocr_result(self, mock_llm, mock_tesseract, supervisor_ctx, db_session, seed_ticket_with_scan):
        ticket = seed_ticket_with_scan
        trigger_ocr(db_session, supervisor_ctx, ticket.ticket_id)
        result = get_ocr_result(db_session, supervisor_ctx, ticket.ticket_id)
        assert result is not None
        assert result["extractedItems"] is not None

    def test_get_ocr_result_not_found(self, supervisor_ctx, db_session, seed_ticket_with_scan):
        result = get_ocr_result(db_session, supervisor_ctx, seed_ticket_with_scan.ticket_id)
        assert result is None
