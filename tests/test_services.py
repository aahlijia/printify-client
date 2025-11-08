"""Tests for service classes."""

import json
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, MagicMock
import responses

from printify_client.services.product_service import ProductService
from printify_client.services.shipping_service import ShippingService
from printify_client.services.order_service import OrderService
from printify_client.client import APIClient
from printify_client.cache import CacheManager
from printify_client.models.product import Product, Variant
from printify_client.models.order import LineItem, Address
from printify_client.exceptions import ValidationError, ShippingCalculationError


# Load test fixtures
fixtures_path = Path(__file__).parent / "fixtures" / "api_responses.json"
with open(fixtures_path) as f:
    FIXTURES = json.load(f)


def test_product_service_get_all_products():
    """Test ProductService.get_all_products() with mocked API responses."""
    # Create mock client that returns empty data list for page 2+ to stop pagination
    mock_client = Mock(spec=APIClient)
    
    call_count = [0]
    
    def mock_get(endpoint, params=None):
        call_count[0] += 1
        # Extract page number from endpoint URL
        if "?page=" in endpoint:
            page = int(endpoint.split("?page=")[1].split("&")[0])
        else:
            page = 1
        
        if page == 1:
            return FIXTURES["product_list_response"]
        else:
            # Return empty data for subsequent pages to stop pagination
            return {"current_page": page, "data": [], "last_page": 1, "total": 2}
    
    mock_client.get.side_effect = mock_get
    
    cache = CacheManager(ttl=10, max_size=10)
    service = ProductService(mock_client, "shop_123", cache)
    
    # Get products
    products = service.get_all_products()
    
    assert len(products) == 2
    assert products[0].id == "prod_001"
    assert products[1].id == "prod_002"
    assert mock_client.get.called


def test_product_service_caching():
    """Test that ProductService caches results."""
    mock_client = Mock(spec=APIClient)
    
    def mock_get(endpoint, params=None):
        # Extract page number from endpoint URL
        if "?page=" in endpoint:
            page = int(endpoint.split("?page=")[1].split("&")[0])
        else:
            page = 1
        
        if page == 1:
            return FIXTURES["product_list_response"]
        else:
            # Return empty data for subsequent pages
            return {"current_page": page, "data": [], "last_page": 1, "total": 2}
    
    mock_client.get.side_effect = mock_get
    
    cache = CacheManager(ttl=10, max_size=10)
    service = ProductService(mock_client, "shop_123", cache)
    
    # First call
    products1 = service.get_all_products()
    call_count_1 = mock_client.get.call_count
    
    # Second call should use cache
    products2 = service.get_all_products()
    call_count_2 = mock_client.get.call_count
    
    assert len(products1) == len(products2)
    assert call_count_1 == call_count_2  # No additional API call


def test_product_service_filter_disabled_variants():
    """Test that products without enabled variants are filtered out."""
    # Create product with no enabled variants
    product_data = {
        "current_page": 1,
        "data": [
            {
                "id": "prod_disabled",
                "title": "Disabled Product",
                "description": "No enabled variants",
                "blueprint_id": 3,
                "print_provider_id": 5,
                "variants": [
                    {"id": 1, "title": "Disabled", "is_enabled": False, "price": 2000}
                ],
                "images": []
            }
        ],
        "last_page": 1,
        "total": 1
    }
    
    mock_client = Mock(spec=APIClient)
    
    def mock_get(endpoint, params=None):
        # Extract page number from endpoint URL
        if "?page=" in endpoint:
            page = int(endpoint.split("?page=")[1].split("&")[0])
        else:
            page = 1
        
        if page == 1:
            return product_data
        else:
            # Return empty data for subsequent pages
            return {"current_page": page, "data": [], "last_page": 1, "total": 1}
    
    mock_client.get.side_effect = mock_get
    
    cache = CacheManager(ttl=10, max_size=10)
    service = ProductService(mock_client, "shop_123", cache)
    
    # Should filter out product with no enabled variants
    products = service.get_all_products(include_disabled=False)
    assert len(products) == 0
    
    # Clear cache for second test
    cache.clear()
    
    # Should include when explicitly requested
    products_all = service.get_all_products(include_disabled=True)
    assert len(products_all) == 1


def test_product_service_get_product_by_id():
    """Test ProductService.get_product_by_id()."""
    mock_client = Mock(spec=APIClient)
    mock_client.get.return_value = FIXTURES["product_response"]
    
    cache = CacheManager(ttl=10, max_size=10)
    service = ProductService(mock_client, "shop_123", cache)
    
    product = service.get_product_by_id("test_product_123")
    
    assert product.id == "test_product_123"
    assert product.title == "Test T-Shirt"
    assert len(product.variants) == 3


def test_shipping_service_calculate_cost():
    """Test ShippingService.calculate_cost() with multiple items."""
    mock_client = Mock(spec=APIClient)
    
    # Mock shipping profile response
    shipping_response = {
        "profiles": [
            {
                "variant_ids": [101, 102],
                "first_item": {"cost": 450},
                "additional_items": {"cost": 200},
                "countries": ["US"]
            }
        ]
    }
    mock_client.get.return_value = shipping_response
    
    cache = CacheManager(ttl=10, max_size=10)
    service = ShippingService(mock_client, cache)
    
    # Create test data
    line_items = [
        LineItem(product_id="test_product_123", variant_id=101, quantity=2)
    ]
    
    address = Address(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        country="US",
        region="CA",
        city="San Francisco",
        zip_code="94102",
        address1="123 Main St"
    )
    
    products = [
        Product(
            id="test_product_123",
            title="Test Product",
            description="Test",
            blueprint_id=3,
            print_provider_id=5,
            variants=[
                Variant(id=101, title="Small", is_enabled=True, price=Decimal("25.00"))
            ],
            images=[]
        )
    ]
    
    # Calculate shipping
    shipping_cost = service.calculate_cost(line_items, address, products)
    
    # First item: $4.50, additional item: $2.00
    # Total: $4.50 + $2.00 = $6.50
    assert shipping_cost.cost == Decimal("6.50")
    assert shipping_cost.currency == "USD"
    assert len(shipping_cost.breakdown) == 1


def test_shipping_service_first_item_pricing():
    """Test shipping cost calculation with first-item and additional-items pricing."""
    mock_client = Mock(spec=APIClient)
    
    shipping_response = {
        "profiles": [
            {
                "variant_ids": [101],
                "first_item": {"cost": 500},
                "additional_items": {"cost": 250},
                "countries": ["US"]
            }
        ]
    }
    mock_client.get.return_value = shipping_response
    
    cache = CacheManager(ttl=10, max_size=10)
    service = ShippingService(mock_client, cache)
    
    address = Address(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        country="US",
        region="CA",
        city="San Francisco",
        zip_code="94102",
        address1="123 Main St"
    )
    
    products = [
        Product(
            id="prod_1",
            title="Product 1",
            description="Test",
            blueprint_id=3,
            print_provider_id=5,
            variants=[Variant(id=101, title="Small", is_enabled=True, price=Decimal("20.00"))],
            images=[]
        )
    ]
    
    # Test with quantity 1 (only first-item cost)
    line_items_1 = [LineItem(product_id="prod_1", variant_id=101, quantity=1)]
    cost_1 = service.calculate_cost(line_items_1, address, products)
    assert cost_1.cost == Decimal("5.00")
    
    # Test with quantity 3 (first-item + 2 additional)
    line_items_3 = [LineItem(product_id="prod_1", variant_id=101, quantity=3)]
    cost_3 = service.calculate_cost(line_items_3, address, products)
    # $5.00 + ($2.50 * 2) = $10.00
    assert cost_3.cost == Decimal("10.00")


def test_shipping_service_missing_profile_error():
    """Test that ShippingCalculationError is raised when profile not found."""
    mock_client = Mock(spec=APIClient)
    
    # Return empty profiles
    shipping_response = {"profiles": []}
    mock_client.get.return_value = shipping_response
    
    cache = CacheManager(ttl=10, max_size=10)
    service = ShippingService(mock_client, cache)
    
    line_items = [LineItem(product_id="prod_1", variant_id=999, quantity=1)]
    address = Address(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        country="US",
        region="CA",
        city="San Francisco",
        zip_code="94102",
        address1="123 Main St"
    )
    
    products = [
        Product(
            id="prod_1",
            title="Product 1",
            description="Test",
            blueprint_id=3,
            print_provider_id=5,
            variants=[Variant(id=999, title="Test", is_enabled=True, price=Decimal("20.00"))],
            images=[]
        )
    ]
    
    try:
        service.calculate_cost(line_items, address, products)
        assert False, "Should have raised ShippingCalculationError"
    except ShippingCalculationError as e:
        assert "No shipping profile found" in str(e)


def test_order_service_create_order():
    """Test OrderService.create_order() with validation."""
    mock_client = Mock(spec=APIClient)
    mock_client.post.return_value = FIXTURES["order_response"]
    
    service = OrderService(mock_client, "shop_123")
    
    line_items = [
        LineItem(product_id="test_product_123", variant_id=101, quantity=2)
    ]
    
    address = Address(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        country="US",
        region="CA",
        city="San Francisco",
        zip_code="94102",
        address1="123 Main St"
    )
    
    order = service.create_order(
        line_items=line_items,
        shipping_address=address,
        external_id="ext_order_001"
    )
    
    assert order.id == "order_12345"
    assert order.external_id == "ext_order_001"
    assert order.status == "pending"
    assert len(order.line_items) == 1
    assert mock_client.post.called


def test_order_service_validation_empty_line_items():
    """Test that ValidationError is raised for empty line items."""
    mock_client = Mock(spec=APIClient)
    service = OrderService(mock_client, "shop_123")
    
    address = Address(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        country="US",
        region="CA",
        city="San Francisco",
        zip_code="94102",
        address1="123 Main St"
    )
    
    try:
        service.create_order(line_items=[], shipping_address=address)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "At least one line item is required" in str(e)


def test_order_service_validation_missing_address_fields():
    """Test that ValidationError is raised for missing address fields."""
    mock_client = Mock(spec=APIClient)
    service = OrderService(mock_client, "shop_123")
    
    line_items = [
        LineItem(product_id="prod_1", variant_id=101, quantity=1)
    ]
    
    # Missing required field (email)
    address = Address(
        first_name="John",
        last_name="Doe",
        email="",  # Empty email
        country="US",
        region="CA",
        city="San Francisco",
        zip_code="94102",
        address1="123 Main St"
    )
    
    try:
        service.create_order(line_items=line_items, shipping_address=address)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "email is required" in str(e)


def test_order_service_validation_invalid_quantity():
    """Test that ValidationError is raised for invalid quantity."""
    mock_client = Mock(spec=APIClient)
    service = OrderService(mock_client, "shop_123")
    
    line_items = [
        LineItem(product_id="prod_1", variant_id=101, quantity=0)  # Invalid quantity
    ]
    
    address = Address(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        country="US",
        region="CA",
        city="San Francisco",
        zip_code="94102",
        address1="123 Main St"
    )
    
    try:
        service.create_order(line_items=line_items, shipping_address=address)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "quantity must be greater than 0" in str(e)
