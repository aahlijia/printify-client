"""
Printify Python Library

A Python library for interacting with the Printify REST API.

This library provides a clean, intuitive interface for managing Printify shops,
products, orders, and shipping calculations. It handles authentication, request
management, response parsing, and data structuring to provide developers with
a clean, Pythonic API for Printify integration.

Example:
    >>> from printify_client import Shop, LineItem, Address
    >>> 
    >>> # Initialize shop
    >>> shop = Shop(shop_id="12345", api_key="your_api_key")
    >>> 
    >>> # Get products
    >>> products = shop.get_products()
    >>> for product in products:
    ...     print(f"{product.title}: ${product.price_range[0]}")
    >>> 
    >>> # Calculate shipping
    >>> items = [LineItem(product_id="prod_123", variant_id=456, quantity=2)]
    >>> address = Address(
    ...     first_name="John",
    ...     last_name="Doe",
    ...     email="john@example.com",
    ...     country="US",
    ...     region="CA",
    ...     city="San Francisco",
    ...     zip_code="94102",
    ...     address1="123 Main St"
    ... )
    >>> shipping = shop.calculate_shipping(items, address)
    >>> print(f"Shipping: {shipping}")
    >>> 
    >>> # Create order
    >>> order = shop.create_order(items, address, external_id="order_12345")
    >>> print(f"Order created: {order.id}")
"""

__version__ = "0.1.0"

# Import main entry point
from printify_client.shop import Shop

# Import model classes
from printify_client.models.product import Product, Variant, Image
from printify_client.models.order import Order, LineItem, Address
from printify_client.models.shipping import ShippingCost, ShippingBreakdown
from printify_client.models.shop import ShopInfo

# Import exception classes
from printify_client.exceptions import (
    PrintifyError,
    AuthenticationError,
    NotFoundError,
    APIError,
    ValidationError,
    ShippingCalculationError,
    TimeoutError,
)

# Explicit exports for better IDE support and documentation
__all__ = [
    # Version
    "__version__",
    # Main entry point
    "Shop",
    # Product models
    "Product",
    "Variant",
    "Image",
    # Order models
    "Order",
    "LineItem",
    "Address",
    # Shipping models
    "ShippingCost",
    "ShippingBreakdown",
    # Shop models
    "ShopInfo",
    # Exceptions
    "PrintifyError",
    "AuthenticationError",
    "NotFoundError",
    "APIError",
    "ValidationError",
    "ShippingCalculationError",
    "TimeoutError",
]
