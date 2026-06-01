"""
Data models for Printify API responses.
"""
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any

from printify_client.models.product import Product, Variant, Image
from printify_client.models.order import Order, LineItem, Address
from printify_client.models.shipping import ShippingCost, ShippingBreakdown
from printify_client.models.shop import ShopInfo


def cents_to_decimal(cents: int) -> Decimal:
    """
    Convert price from cents (integer) to decimal currency value.
    
    Args:
        cents: Price in cents as integer
        
    Returns:
        Decimal value representing currency amount
        
    Example:
        >>> cents_to_decimal(1999)
        Decimal('19.99')
    """
    return Decimal(cents) / 100


def parse_datetime(iso_string: str) -> datetime:
    """
    Parse ISO format datetime string to datetime object.
    
    Args:
        iso_string: ISO format datetime string
        
    Returns:
        datetime object
        
    Example:
        >>> parse_datetime("2024-01-15T10:30:00Z")
        datetime.datetime(2024, 1, 15, 10, 30, 0)
    """
    # Handle both with and without timezone
    if iso_string.endswith('Z'):
        iso_string = iso_string[:-1] + '+00:00'
    return datetime.fromisoformat(iso_string)


def parse_product(data: Dict[str, Any]) -> 'Product':
    """
    Parse API product response to Product model.
    
    Args:
        data: Raw API response dictionary
        
    Returns:
        Product model instance
    """
    variants = [parse_variant(v) for v in data.get('variants', [])]
    images = [parse_image(i) for i in data.get('images', [])]
    
    return Product(
        id=data['id'],
        title=data['title'],
        description=data.get('description', ''),
        blueprint_id=data['blueprint_id'],
        print_provider_id=data['print_provider_id'],
        variants=variants,
        images=images
    )


def parse_variant(data: Dict[str, Any]) -> 'Variant':
    """
    Parse API variant response to Variant model.
    
    Args:
        data: Raw API response dictionary
        
    Returns:
        Variant model instance
    """
    return Variant(
        id=data['id'],
        title=data['title'],
        is_enabled=data['is_enabled'],
        price=cents_to_decimal(data['price'])
    )


def parse_image(data: Dict[str, Any]) -> 'Image':
    """
    Parse API image response to Image model.
    
    Args:
        data: Raw API response dictionary
        
    Returns:
        Image model instance
    """
    return Image(
        src=data['src'],
        variant_ids=data.get('variant_ids', []),
        position=data['position'],
        is_default=data.get('is_default', False)
    )


def parse_order(data: Dict[str, Any]) -> 'Order':
    """
    Parse API order response to Order model.
    
    Args:
        data: Raw API response dictionary
        
    Returns:
        Order model instance
    """
    line_items = [parse_line_item(item) for item in data.get('line_items', [])]
    shipping_address = parse_address(data.get('address_to', {}))

    created_at_raw = data.get('created_at')
    try:
        created_at = (
            parse_datetime(created_at_raw)
            if created_at_raw
            else datetime.now()
        )
    except (ValueError, AttributeError):
        created_at = datetime.now()

    return Order(
        id=data['id'],
        external_id=data.get('external_id'),
        status=data.get('status', 'pending'),
        created_at=created_at,
        line_items=line_items,
        shipping_address=shipping_address
    )


def parse_line_item(data: Dict[str, Any]) -> 'LineItem':
    """
    Parse API line item response to LineItem model.
    
    Args:
        data: Raw API response dictionary
        
    Returns:
        LineItem model instance
    """
    return LineItem(
        product_id=data['product_id'],
        variant_id=data['variant_id'],
        quantity=data['quantity']
    )


def parse_address(data: Dict[str, Any]) -> 'Address':
    """
    Parse API address response to Address model.
    
    Args:
        data: Raw API response dictionary
        
    Returns:
        Address model instance
    """
    return Address(
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        email=data.get('email', ''),
        country=data.get('country', ''),
        region=data.get('region', ''),
        city=data.get('city', ''),
        zip_code=data.get('zip', ''),
        address1=data.get('address1', ''),
        address2=data.get('address2'),
        phone=data.get('phone')
    )


def parse_shipping_cost(data: Dict[str, Any]) -> 'ShippingCost':
    """
    Parse API shipping cost response to ShippingCost model.
    
    Args:
        data: Raw API response dictionary
        
    Returns:
        ShippingCost model instance
    """
    breakdown = [parse_shipping_breakdown(item) for item in data.get('breakdown', [])]
    
    return ShippingCost(
        cost=cents_to_decimal(data['cost']),
        currency=data.get('currency', 'USD'),
        breakdown=breakdown
    )


def parse_shipping_breakdown(data: Dict[str, Any]) -> 'ShippingBreakdown':
    """
    Parse API shipping breakdown response to ShippingBreakdown model.
    
    Args:
        data: Raw API response dictionary
        
    Returns:
        ShippingBreakdown model instance
    """
    return ShippingBreakdown(
        product_id=data['product_id'],
        variant_id=data['variant_id'],
        quantity=data['quantity'],
        cost=cents_to_decimal(data['cost'])
    )


def parse_shop_info(data: Dict[str, Any]) -> 'ShopInfo':
    """
    Parse API shop response to ShopInfo model.
    
    Args:
        data: Raw API response dictionary
        
    Returns:
        ShopInfo model instance
    """
    return ShopInfo(
        id=data['id'],
        title=data['title'],
        sales_channel=data.get('sales_channel')
    )


# Export all models and utilities
__all__ = [
    # Utility functions
    'cents_to_decimal',
    'parse_datetime',
    'parse_product',
    'parse_variant',
    'parse_image',
    'parse_order',
    'parse_line_item',
    'parse_address',
    'parse_shipping_cost',
    'parse_shipping_breakdown',
    'parse_shop_info',
    # Models
    'Product',
    'Variant',
    'Image',
    'Order',
    'LineItem',
    'Address',
    'ShippingCost',
    'ShippingBreakdown',
    'ShopInfo',
]
