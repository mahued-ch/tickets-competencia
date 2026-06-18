from app.schemas.security import SecurityContext
from app.models.ticket import Ticket


def can_view_ticket(ctx: SecurityContext, ticket: Ticket) -> bool:
    if ctx.role_code in {"SUPERVISOR", "ADMIN"}:
        return True
    ticket_store_codes = {ts.store_code for ts in ticket.stores}
    return len(ticket_store_codes.intersection(set(ctx.store_codes))) > 0


def require_admin(ctx: SecurityContext) -> None:
    if ctx.role_code != "ADMIN":
        raise PermissionError("Only ADMIN can access this resource")
