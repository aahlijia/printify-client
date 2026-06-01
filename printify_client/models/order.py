"""
Order-related data models.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class LineItem:
    """
    Represents an item in an order or cart.
    
    Attributes:
        product_id: Printify product identifier
        variant_id: Product variant identifier
        quantity: Number of items
    """
    product_id: str
    variant_id: int
    quantity: int

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to API request format.
        
        Returns:
            Dictionary formatted for Printify API requests
        """
        return {
            'product_id': self.product_id,
            'variant_id': self.variant_id,
            'quantity': self.quantity
        }

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"LineItem(product={self.product_id}, variant={self.variant_id}, qty={self.quantity})"


@dataclass
class Address:
    """
    Represents a shipping address.
    
    Attributes:
        first_name: Recipient first name
        last_name: Recipient last name
        email: Recipient email address
        country: Country code (e.g., "US")
        region: State/province/region
        city: City name
        zip_code: Postal/ZIP code
        address1: Primary address line
        address2: Secondary address line (optional)
        phone: Phone number (optional)
    """
    first_name: str
    last_name: str
    email: str
    country: str
    region: str
    city: str
    zip_code: str
    address1: str
    address2: Optional[str] = None
    phone: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to API request format.
        
        Returns:
            Dictionary formatted for Printify API requests
        """
        data = {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'country': self.country,
            'region': self.region,
            'city': self.city,
            'zip': self.zip_code,
            'address1': self.address1
        }

        if self.address2:
            data['address2'] = self.address2
        if self.phone:
            data['phone'] = self.phone

        return data

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"{self.first_name} {self.last_name}, {self.city}, {self.region} {self.zip_code}, {self.country}"


@dataclass
class Order:
    """
    Represents a Printify order.
    
    Attributes:
        id: Printify order identifier
        external_id: External order reference (optional)
        status: Order status (e.g., "pending", "processing")
        created_at: Order creation timestamp
        line_items: List of items in the order
        shipping_address: Shipping destination address
    """
    id: str
    external_id: Optional[str]
    status: str
    created_at: datetime
    line_items: List[LineItem]
    shipping_address: Address

    @property
    def is_pending(self) -> bool:
        """
        Check if order is in pending status.
        
        Returns:
            True if order status is "pending", False otherwise
        """
        return self.status == 'pending'

    def __str__(self) -> str:
        """String representation for debugging."""
        item_count = sum(item.quantity for item in self.line_items)
        external_ref = f" (ext: {self.external_id})" if self.external_id else ""
        return f"Order {self.id}{external_ref}: {item_count} items, status={self.status}"
