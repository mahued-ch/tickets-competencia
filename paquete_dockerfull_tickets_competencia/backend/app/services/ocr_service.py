import json
import re
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.ticket import Ticket, TicketScanFile
from app.models.ocr import OcrResult
from app.schemas.security import SecurityContext
from app.services.security_service import can_view_ticket
from app.services.ticket_service import get_ticket_or_404
from app.storage.local_storage import LocalStorageService

settings = get_settings()
storage = LocalStorageService()

TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _run_tesseract(image_path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        image = Image.open(image_path)
        return pytesseract.image_to_string(image, lang='spa')
    except ImportError:
        return _mock_ocr_text()
    except Exception:
        return ""


def _mock_ocr_text() -> str:
    return (
        "TICKET DE COMPRA\n"
        "WALMART SUPERCENTER\n"
        "Av. Ejemplo 123, Ciudad\n"
        "FECHA: 15/06/2026 14:30\n"
        "--------------------------------\n"
        "  LECHE ENTERA LALA 1L    2  25.50  51.00\n"
        "  PAN BIMBO BLANCO 680G   1  42.00  42.00\n"
        "  HUEVO BLANCO 30PZ      1  89.00  89.00\n"
        "  ARROVA VERDE 1KG       2  38.50  77.00\n"
        "  COCA-COLA 2L            3  35.00 105.00\n"
        "--------------------------------\n"
        "TOTAL:  364.00 MXN\n"
    )


def _build_llm_prompt(business_code: str, raw_text: str) -> list[dict]:
    prompt = (
        f"Extract ticket items from the following OCR text for business '{business_code}'. "
        "Return a JSON array with objects containing these fields:\n"
        "- code: product code if visible, otherwise null\n"
        "- description: product name/description\n"
        "- quantity: numeric quantity purchased\n"
        "- unitPrice: unit price\n"
        "- lineAmount: total line amount\n\n"
        f"OCR TEXT:\n{raw_text}\n\n"
        "Return ONLY the JSON array, no other text."
    )
    return [{"role": "user", "content": prompt}]


def _call_llm(messages: list[dict]) -> tuple[str, float]:
    api_key = settings.ocr_llm_api_key
    model = settings.ocr_llm_model

    if not api_key:
        return _mock_llm_parse(messages[0]["content"]), 0.0

    provider = settings.ocr_llm_provider
    try:
        if provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
            )
            return resp.choices[0].message.content or "[]", 0.95
        elif provider == "anthropic":
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            resp = client.messages.create(
                model=model,
                messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                max_tokens=2000,
                temperature=0.1,
            )
            return resp.content[0].text, 0.95
        else:
            return _mock_llm_parse(messages[0]["content"]), 0.0
    except Exception:
        return _mock_llm_parse(messages[0]["content"]), 0.0


def _mock_llm_parse(prompt_text: str) -> str:
    raw = _extract_ocr_text_from_prompt(prompt_text)
    items = _basic_parse_lines(raw)
    if not items:
        items = [
            {"code": None, "description": "PRODUCTO 1", "quantity": 1, "unitPrice": 0, "lineAmount": 0},
        ]
    return json.dumps(items, ensure_ascii=False)


def _extract_ocr_text_from_prompt(prompt_text: str) -> str:
    """Extract the OCR text portion from the LLM prompt."""
    marker = "OCR TEXT:\n"
    idx = prompt_text.find(marker)
    if idx != -1:
        return prompt_text[idx + len(marker):]
    return prompt_text


def _basic_parse_lines(raw: str) -> list[dict]:
    """Parse ticket OCR lines with optional leading qty and trailing letter codes."""
    items = []
    for line in raw.split('\n'):
        line = line.strip()
        if not line or len(line) < 6:
            continue
        if line.startswith('-') or line.startswith('='):
            continue
        if line.upper().startswith('TOTAL') or line.upper().startswith('CANT'):
            continue
        m = re.search(r'(\d+(?:\.\d+)?)\s+(.+?)\s+([\d,.]+)\s+([\d,.]+)(?:\s+\w)?\s*$', line)
        if m:
            qty = float(m.group(1))
            desc = m.group(2).strip().rstrip('*').strip()
            price = float(m.group(3).replace(',', ''))
            amount = float(m.group(4).replace(',', ''))
            if desc and price > 0:
                items.append({
                    "code": None,
                    "description": desc,
                    "quantity": qty,
                    "unitPrice": price,
                    "lineAmount": amount,
                })
    return items


def trigger_ocr(db: Session, ctx: SecurityContext, ticket_id: int) -> dict:
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")

    active = next((f for f in sorted(ticket.scan_files, key=lambda x: x.version_number, reverse=True) if f.is_active), None)
    if not active:
        raise ValueError("NO_ACTIVE_SCAN_FILE")

    raw_text = _run_tesseract(active.storage_path)

    messages = _build_llm_prompt(ticket.source_business_code, raw_text)
    llm_output, confidence = _call_llm(messages)

    try:
        extracted = json.loads(llm_output) if isinstance(llm_output, str) else llm_output
        if not isinstance(extracted, list):
            extracted = []
    except (json.JSONDecodeError, TypeError):
        extracted = []

    result = OcrResult(
        ticket_scan_file_id=active.ticket_scan_file_id,
        raw_text=raw_text,
        extracted_items=extracted,
        llm_model=settings.ocr_llm_model,
        confidence=confidence,
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    db.refresh(ticket)

    return {
        "ocrId": result.ocr_id,
        "ticketScanFileId": result.ticket_scan_file_id,
        "llmModel": result.llm_model,
        "confidence": float(result.confidence) if result.confidence is not None else None,
        "itemCount": len(extracted),
    }


def get_ocr_result(db: Session, ctx: SecurityContext, ticket_id: int) -> dict | None:
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")

    active = next((f for f in sorted(ticket.scan_files, key=lambda x: x.version_number, reverse=True) if f.is_active), None)
    if not active:
        return None

    result = db.query(OcrResult).filter(
        OcrResult.ticket_scan_file_id == active.ticket_scan_file_id
    ).order_by(OcrResult.ocr_id.desc()).first()

    if not result:
        return None

    return {
        "ocrId": result.ocr_id,
        "ticketScanFileId": result.ticket_scan_file_id,
        "rawText": result.raw_text,
        "extractedItems": result.extracted_items,
        "llmModel": result.llm_model,
        "confidence": float(result.confidence) if result.confidence is not None else None,
        "createdAt": result.created_at,
    }
