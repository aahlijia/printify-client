"""
Shipping-related data models.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import List


@dataclass
class ShippingBreakdown:
    """
    Shipping cost breakdown for a single product.
    
    Attributes:
        product_id: Printify product identifier
        variant_id: Product variant identifier
        quantity: Number of items
        cost: Shipping cost for this item in decimal currency
    """
    product_id: str
    variant_id: int
    quantity: int
    cost: Decimal

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"ShippingBreakdown(product={self.product_id}, variant={self.variant_id}, qty={self.quantity}, cost=${self.cost:.2f})"


@dataclass
class ShippingCost:
    """
    Represents calculated shipping cost.
    
    Attributes:
        cost: Total shipping cost in decimal currency
        currency: Currency code (e.g., "USD")
        breakdown: Per-item cost breakdown
    """
    cost: Decimal
    currency: str
    breakdown: List[ShippingBreakdown]

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"{self.cost:.2f} {self.currency}"
