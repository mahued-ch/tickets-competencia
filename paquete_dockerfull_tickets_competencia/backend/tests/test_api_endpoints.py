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


def test_coverage_forbidden_for_store_user(client_with_store_user):
    res = client_with_store_user.get("/api/v1/tickets/coverage")
    assert res.status_code == 403


def test_audit_events_endpoint(client_with_supervisor):
    res = client_with_supervisor.get("/api/v1/audit/events")
    assert res.status_code == 200
    data = res.json()
    assert 'data' in data
