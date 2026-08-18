"""Service layer — the business rules that live between the API and the models.

Keeping cross-module effects here (instead of inside API handlers) is how the
modular monolith keeps its boundaries: the sales flow asks the inventory service
to adjust stock and the accounting service to record money, rather than reaching
into those tables itself.
"""
