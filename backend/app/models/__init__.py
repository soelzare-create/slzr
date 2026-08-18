"""ORM models for the DaranX data model.

Importing this package registers every table on the declarative ``Base``.
"""
from app.models.accounting import FinancialDocument
from app.models.activity import Activity, ActivityItem, ProjectStage
from app.models.customer import Customer
from app.models.inventory import InventoryMovement, ProductModel, UnitItem
from app.models.invoice import Invoice
from app.models.support import Ticket
from app.models.user import User

__all__ = [
    "User",
    "Customer",
    "Activity",
    "ProjectStage",
    "ActivityItem",
    "ProductModel",
    "UnitItem",
    "InventoryMovement",
    "Invoice",
    "FinancialDocument",
    "Ticket",
]
