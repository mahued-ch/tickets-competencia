import pytest
from app.models.ticket import Ticket
from app.services.ticket_service import search_tickets, get_ticket_detail, get_coverage_stats


class TestSearchTickets:
    def test_search_all_for_supervisor(self, supervisor_ctx, db_session, seed_ticket):
        items, meta = search_tickets(db_session, supervisor_ctx, {})
        assert len(items) == 1
        assert meta['totalRecords'] == 1

    def test_search_all_for_store_user(self, store_user_ctx, db_session, seed_ticket):
        items, meta = search_tickets(db_session, store_user_ctx, {})
        assert len(items) == 1

    def test_search_filter_by_status(self, supervisor_ctx, db_session, seed_ticket):
        items, meta = search_tickets(db_session, supervisor_ctx, {'sourceStatusCode': '9'})
        assert len(items) == 1
        items2, _ = search_tickets(db_session, supervisor_ctx, {'sourceStatusCode': 'X'})
        assert len(items2) == 0

    def test_search_pagination(self, supervisor_ctx, db_session, seed_ticket):
        items, meta = search_tickets(db_session, supervisor_ctx, {'page': 1, 'pageSize': 20})
        assert len(items) == 1
        assert meta['totalPages'] == 1
        items2, meta2 = search_tickets(db_session, supervisor_ctx, {'page': 2, 'pageSize': 20})
        assert len(items2) == 0


class TestGetTicketDetail:
    def test_get_detail_for_supervisor(self, supervisor_ctx, db_session, seed_ticket):
        data = get_ticket_detail(db_session, supervisor_ctx, seed_ticket.ticket_id)
        assert data['ticket'].sourceTicketCode == 'TKT001'
        assert data['scanFileSummary']['exists'] is False

    def test_get_detail_not_found(self, supervisor_ctx, db_session):
        with pytest.raises(LookupError):
            get_ticket_detail(db_session, supervisor_ctx, 99999)

    def test_get_detail_forbidden_for_store_user(self, store_user_ctx, db_session, seed_ticket):
        # remove ticket stores
        from app.models.ticket import TicketStore
        db_session.query(TicketStore).filter(TicketStore.ticket_id == seed_ticket.ticket_id).delete()
        db_session.commit()
        db_session.refresh(seed_ticket)
        with pytest.raises(PermissionError):
            get_ticket_detail(db_session, store_user_ctx, seed_ticket.ticket_id)


class TestCoverage:
    def test_coverage_for_supervisor(self, supervisor_ctx, db_session, seed_ticket):
        data = get_coverage_stats(db_session, supervisor_ctx)
        assert data['totalTickets'] == 1
        assert data['byStatus'].get('9') == 1

    def test_coverage_for_store_user(self, store_user_ctx, db_session):
        data = get_coverage_stats(db_session, store_user_ctx)
        assert data['totalTickets'] == 0
        assert data['byStatus'] == {}
        assert data['byScanStatus'] == {}
        assert data['byStore'] == []
        assert data['byBusiness'] == []
