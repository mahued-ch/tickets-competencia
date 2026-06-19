from app.services.security_service import can_view_ticket, require_admin


def test_supervisor_can_view_any_ticket(supervisor_ctx, seed_ticket):
    assert can_view_ticket(supervisor_ctx, seed_ticket) is True


def test_admin_can_view_any_ticket(admin_ctx, seed_ticket):
    assert can_view_ticket(admin_ctx, seed_ticket) is True


def test_store_user_can_view_own_store_ticket(store_user_ctx, seed_ticket):
    assert can_view_ticket(store_user_ctx, seed_ticket) is True


def test_store_user_cannot_view_other_store_ticket(store_user_ctx, seed_ticket, db_session):
    from app.models.ticket import TicketStore
    # remove store_user's stores from ticket
    db_session.query(TicketStore).filter(TicketStore.ticket_id == seed_ticket.ticket_id).delete()
    db_session.commit()
    db_session.refresh(seed_ticket)
    assert can_view_ticket(store_user_ctx, seed_ticket) is False


def test_store_user_cannot_view_confirmed_ticket(store_user_ctx, seed_ticket_with_scan, db_session):
    t = seed_ticket_with_scan
    t.scan_status = 'FILE_CONFIRMED'
    db_session.commit()
    assert can_view_ticket(store_user_ctx, t) is False


def test_supervisor_can_view_confirmed_ticket(supervisor_ctx, seed_ticket_with_scan, db_session):
    t = seed_ticket_with_scan
    t.scan_status = 'FILE_CONFIRMED'
    db_session.commit()
    assert can_view_ticket(supervisor_ctx, t) is True


def test_require_admin_passes_for_admin(admin_ctx):
    require_admin(admin_ctx)


def test_require_admin_raises_for_supervisor(supervisor_ctx):
    import pytest
    with pytest.raises(PermissionError):
        require_admin(supervisor_ctx)


def test_require_admin_raises_for_store_user(store_user_ctx):
    import pytest
    with pytest.raises(PermissionError):
        require_admin(store_user_ctx)
