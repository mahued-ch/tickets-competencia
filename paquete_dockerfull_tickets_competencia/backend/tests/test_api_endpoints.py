def test_health_endpoint(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data['success'] is True


def test_tickets_list(client_with_supervisor, seed_ticket):
    res = client_with_supervisor.get("/api/v1/tickets")
    assert res.status_code == 200
    data = res.json()
    assert len(data['data']) == 1


def test_ticket_detail(client_with_supervisor, seed_ticket):
    res = client_with_supervisor.get(f"/api/v1/tickets/{seed_ticket.ticket_id}")
    assert res.status_code == 200
    data = res.json()
    assert data['data']['ticket']['sourceTicketCode'] == 'TKT001'


def test_ticket_items(client_with_supervisor, seed_ticket):
    res = client_with_supervisor.get(f"/api/v1/tickets/{seed_ticket.ticket_id}/items")
    assert res.status_code == 200
    assert len(res.json()['data']) == 1


def test_ticket_stores(client_with_supervisor, seed_ticket):
    res = client_with_supervisor.get(f"/api/v1/tickets/{seed_ticket.ticket_id}/stores")
    assert res.status_code == 200
    assert len(res.json()['data']) == 2


def test_ticket_not_found(client_with_supervisor):
    res = client_with_supervisor.get("/api/v1/tickets/99999")
    assert res.status_code == 404


def test_coverage_endpoint(client_with_supervisor, seed_ticket):
    res = client_with_supervisor.get("/api/v1/tickets/coverage")
    assert res.status_code == 200
    data = res.json()['data']
    assert data['totalTickets'] >= 1


def test_coverage_for_store_user(client_with_store_user):
    res = client_with_store_user.get("/api/v1/tickets/coverage")
    assert res.status_code == 200
    data = res.json()['data']
    assert data['totalTickets'] >= 0
    assert data['byStatus'] == {}
    assert data['byScanStatus'] == {}
    assert data['byStore'] == []
    assert data['byBusiness'] == []


def test_audit_events_endpoint(client_with_supervisor):
    res = client_with_supervisor.get("/api/v1/audit/events")
    assert res.status_code == 200
    data = res.json()
    assert 'data' in data


# ── Catalog CSV endpoints ────────────────────────────────

def test_catalog_template_competitor_stores(client_with_admin):
    res = client_with_admin.get("/api/v1/catalogs/competitor-stores/template")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "business_code" in res.text


def test_catalog_template_unknown(client_with_admin):
    res = client_with_admin.get("/api/v1/catalogs/invalid/template")
    assert res.status_code == 404


def test_catalog_import_csv(client_with_admin):
    csv = "business_code,store_code,store_name\nWMT,1001,Walmart Test\nBRS,2001,Bodega Test\n"
    res = client_with_admin.post(
        "/api/v1/catalogs/competitor-stores/import",
        files={"file": ("test.csv", csv, "text/csv")},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["imported"] == 2
    assert data["errors"] == []


def test_catalog_import_invalid_file_type(client_with_admin):
    res = client_with_admin.post(
        "/api/v1/catalogs/competitor-stores/import",
        files={"file": ("test.txt", "a,b", "text/plain")},
    )
    assert res.status_code == 400


def test_catalog_import_unknown_catalog(client_with_admin):
    csv = "a,b\n1,2\n"
    res = client_with_admin.post(
        "/api/v1/catalogs/invalid/import",
        files={"file": ("test.csv", csv, "text/csv")},
    )
    assert res.status_code == 404


def test_catalog_forbidden_for_store_user(client_with_store_user):
    res = client_with_store_user.get("/api/v1/catalogs/competitor-stores/template")
    assert res.status_code == 403

    csv = "business_code,store_code\nWMT,1001\n"
    res = client_with_store_user.post(
        "/api/v1/catalogs/competitor-stores/import",
        files={"file": ("test.csv", csv, "text/csv")},
    )
    assert res.status_code == 403


# ── OCR endpoints ────────────────────────────────────────

def test_ocr_trigger_no_scan_file(client_with_supervisor, seed_ticket):
    res = client_with_supervisor.post(f"/api/v1/tickets/{seed_ticket.ticket_id}/ocr")
    assert res.status_code == 409
    assert "NO_ACTIVE_SCAN_FILE" in res.text


def test_ocr_get_not_found(client_with_supervisor, seed_ticket_with_scan):
    res = client_with_supervisor.get(f"/api/v1/tickets/{seed_ticket_with_scan.ticket_id}/ocr")
    assert res.status_code == 404


# ── Enrichment endpoints ─────────────────────────────────

def test_enrichment_trigger_no_ocr(client_with_supervisor, seed_ticket_with_scan):
    res = client_with_supervisor.post(f"/api/v1/tickets/{seed_ticket_with_scan.ticket_id}/enrichment")
    assert res.status_code == 409
    assert "NO_OCR_RESULT" in res.text


def test_enrichment_preview_not_found(client_with_supervisor, seed_ticket_with_scan):
    res = client_with_supervisor.get(f"/api/v1/tickets/{seed_ticket_with_scan.ticket_id}/enrichment-preview")
    assert res.status_code == 404
