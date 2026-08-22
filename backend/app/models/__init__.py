"""ORM models for the DaranX data model.

Importing this package registers every table on the declarative ``Base``.
"""
from app.models.accounting import FinancialDocument
from app.models.activity import Activity, ProjectStage
from app.models.inventory import ProductModel, StockItem
from app.models.invoice import Invoice, InvoiceItem
from app.models.party import Party, PartyContact
from app.models.purchase import Purchase, PurchaseItem
from app.models.support import Ticket
from app.models.user import User

__all__ = [
    "User",
    "Party",
    "PartyContact",
    "Activity",
    "ProjectStage",
    "ProductModel",
    "StockItem",
    "Purchase",
    "PurchaseItem",
    "Invoice",
    "InvoiceItem",
    "FinancialDocument",
    "Ticket",
]
