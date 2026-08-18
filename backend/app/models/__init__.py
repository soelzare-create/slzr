"""ORM models for the DaranX data model.

Importing this package registers every table on the declarative ``Base``.
"""
from app.models.accounting import FinancialDocument
from app.models.activity import Activity, ActivityItem, ProjectStage
from app.models.inventory import InventoryMovement, ProductModel, UnitItem
from app.models.invoice import Invoice
from app.models.party import Party
from app.models.purchase import Purchase, PurchaseItem
from app.models.support import Ticket
from app.models.user import User

__all__ = [
    "User",
    "Party",
    "Activity",
    "ProjectStage",
    "ActivityItem",
    "ProductModel",
    "UnitItem",
    "InventoryMovement",
    "Purchase",
    "PurchaseItem",
    "Invoice",
    "FinancialDocument",
    "Ticket",
]
