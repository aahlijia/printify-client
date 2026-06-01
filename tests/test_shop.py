"""Tests for Shop class (integration tests)."""

import os
import json
from pathlib import Path
from decimal import Decimal
import responses

from printify_client.shop import Shop
from printify_client.models.order import LineItem, Address
from printify_client.exceptions import ValidationError, AuthenticationError, NotFoundError


# Load test fixtures
fixtures_path = Path(__file__).parent / "fixtures" / "api_responses.json"
with open(fixtures_path) as f:
    FIXTURES = json.load(f)


@responses.activate
def test_shop_initialization_with_shop_id():
    """Test Shop initialization with shop_id."""
    # Mock shops list (needed for Shop initialization)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops.json",
        json=FIXTURES["shop_list_response"],
        status=200,
    )
    
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123.json",
        json=FIXTURES["shop_info_response"],
        status=200,
    )
    
    shop = Shop(shop_id="shop_123", api_key="test_api_key")
    
    assert shop.shop_id == "shop_123"
    assert shop.client is not None
    assert shop.cache_manager is not None


@responses.activate
def test_shop_initialization_with_shop_name():
    """Test Shop initialization with shop_name."""
    # Mock shop list response
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops.json",
        json=FIXTURES["shop_list_response"],
        status=200,
    )
    
    # Mock shop info response
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123.json",
        json=FIXTURES["shop_info_response"],
        status=200,
    )
    
    shop = Shop(shop_name="Test Shop", api_key="test_api_key")
    
    assert shop.shop_id == "shop_123"
    assert shop._shop_info.title == "Test Shop"


@responses.activate
def test_shop_initialization_with_env_api_key():
    """Test Shop initialization using environment variable for API key."""
    # Set environment variable
    os.environ['PRINTIFY_API_KEY'] = 'env_api_key'
    
    # Mock shops list (needed for Shop initialization)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops.json",
        json=FIXTURES["shop_list_response"],
        status=200,
    )
    
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123.json",
        json=FIXTURES["shop_info_response"],
        status=200,
    )
    
    try:
        shop = Shop(shop_id="shop_123")
        assert shop.client is not None
        # Verify the API key was used
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["Authorization"] == "Bearer env_api_key"
    finally:
        # Clean up environment variable
        del os.environ['PRINTIFY_API_KEY']


def test_shop_initialization_missing_shop_identifier():
    """Test that ValidationError is raised when neither shop_id nor shop_name provided."""
    try:
        Shop(api_key="test_api_key")
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "shop_id or shop_name must be provided" in str(e)


def test_shop_initialization_missing_api_key():
    """Test that ValidationError is raised when API key is missing."""
    # Ensure environment variable is not set
    if 'PRINTIFY_API_KEY' in os.environ:
        del os.environ['PRINTIFY_API_KEY']
    
    try:
        Shop(shop_id="shop_123")
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "API key must be provided" in str(e)


@responses.activate
def test_shop_initialization_invalid_shop_name():
    """Test that NotFoundError is raised for invalid shop name."""
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops.json",
        json=FIXTURES["shop_list_response"],
        status=200,
    )
    
    try:
        Shop(shop_name="Nonexistent Shop", api_key="test_api_key")
        assert False, "Should have raised NotFoundError"
    except NotFoundError as e:
        assert "Nonexistent Shop" in str(e)


@responses.activate
def test_shop_get_products():
    """Test get_products() returns list of Product objects."""
    # Mock shops list (needed for Shop initialization)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops.json",
        json=FIXTURES["shop_list_response"],
        status=200,
    )
    
    # Mock shop info
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123.json",
        json=FIXTURES["shop_info_response"],
        status=200,
    )
    
    # Mock products list (single page; last_page=1 in the fixture)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123/products.json",
        json=FIXTURES["product_list_response"],
        status=200,
    )

    shop = Shop(shop_id="shop_123", api_key="test_api_key")
    products = shop.get_products()
    
    assert len(products) == 2
    assert products[0].id == "prod_001"
    assert products[0].title == "Product 1"
    assert products[1].id == "prod_002"


@responses.activate
def test_shop_get_product():
    """Test get_product() returns a single Product object."""
    # Mock shops list (needed for Shop initialization)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops.json",
        json=FIXTURES["shop_list_response"],
        status=200,
    )
    
    # Mock shop info
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123.json",
        json=FIXTURES["shop_info_response"],
        status=200,
    )
    
    # Mock single product
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123/products/test_product_123.json",
        json=FIXTURES["product_response"],
        status=200,
    )
    
    shop = Shop(shop_id="shop_123", api_key="test_api_key")
    product = shop.get_product("test_product_123")
    
    assert product.id == "test_product_123"
    assert product.title == "Test T-Shirt"
    assert len(product.variants) == 3


@responses.activate
def test_shop_filter_products():
    """Test filter_products() filters by attributes."""
    # Mock shops list (needed for Shop initialization)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops.json",
        json=FIXTURES["shop_list_response"],
        status=200,
    )
    
    # Mock shop info
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123.json",
        json=FIXTURES["shop_info_response"],
        status=200,
    )
    
    # Mock products list (single page; last_page=1 in the fixture)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123/products.json",
        json=FIXTURES["product_list_response"],
        status=200,
    )

    shop = Shop(shop_id="shop_123", api_key="test_api_key")

    # Filter by blueprint_id
    filtered = shop.filter_products(blueprint_id=3)
    assert len(filtered) == 1
    assert filtered[0].blueprint_id == 3


@responses.activate
def test_shop_calculate_shipping():
    """Test calculate_shipping() returns ShippingCost."""
    # Mock shops list (needed for Shop initialization)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops.json",
        json=FIXTURES["shop_list_response"],
        status=200,
    )
    
    # Mock shop info
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123.json",
        json=FIXTURES["shop_info_response"],
        status=200,
    )
    
    # Mock the single product referenced by the line item. Shipping
    # calculation fetches only the products in the order, not the catalog.
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123/products/test_product_123.json",
        json=FIXTURES["product_response"],
        status=200,
    )

    # Mock shipping profile
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/catalog/blueprints/3/print_providers/5/shipping.json",
        json={
            "profiles": [
                {
                    "variant_ids": [101, 102, 103],
                    "first_item": {"cost": 450},
                    "additional_items": {"cost": 200},
                    "countries": ["US"]
                }
            ]
        },
        status=200,
    )
    
    shop = Shop(shop_id="shop_123", api_key="test_api_key")
    
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
    
    shipping_cost = shop.calculate_shipping(line_items, address)
    
    assert shipping_cost.cost == Decimal("6.50")  # $4.50 + $2.00
    assert shipping_cost.currency == "USD"
    assert len(shipping_cost.breakdown) == 1


@responses.activate
def test_shop_create_order():
    """Test create_order() returns Order object."""
    # Mock shops list (needed for Shop initialization)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops.json",
        json=FIXTURES["shop_list_response"],
        status=200,
    )
    
    # Mock shop info
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123.json",
        json=FIXTURES["shop_info_response"],
        status=200,
    )
    
    # Mock order creation
    responses.add(
        responses.POST,
        "https://api.printify.com/v1/shops/shop_123/orders.json",
        json=FIXTURES["order_response"],
        status=201,
    )
    
    shop = Shop(shop_id="shop_123", api_key="test_api_key")
    
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
    
    order = shop.create_order(
        line_items=line_items,
        shipping_address=address,
        external_id="ext_order_001"
    )
    
    assert order.id == "order_12345"
    assert order.external_id == "ext_order_001"
    assert order.status == "pending"
    assert len(order.line_items) == 1


@responses.activate
def test_shop_clear_cache():
    """Test clear_cache() clears cached data."""
    # Mock shops list (needed for Shop initialization)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops.json",
        json=FIXTURES["shop_list_response"],
        status=200,
    )
    
    # Mock shop info
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123.json",
        json=FIXTURES["shop_info_response"],
        status=200,
    )
    
    # Mock products list (single page; one registration is reused for every
    # matching request, so it serves all get_products() calls in this test)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123/products.json",
        json=FIXTURES["product_list_response"],
        status=200,
    )

    shop = Shop(shop_id="shop_123", api_key="test_api_key", enable_cache=True)
    
    # First call - should hit API
    products1 = shop.get_products()
    call_count_1 = len([c for c in responses.calls if 'products.json' in c.request.url])
    
    # Second call - should use cache
    products2 = shop.get_products()
    call_count_2 = len([c for c in responses.calls if 'products.json' in c.request.url])
    
    assert call_count_1 == call_count_2  # No new API call
    
    # Clear cache
    shop.clear_cache()
    
    # Third call - should hit API again
    products3 = shop.get_products()
    call_count_3 = len([c for c in responses.calls if 'products.json' in c.request.url])
    
    assert call_count_3 == call_count_2 + 1  # New API call after cache clear


@responses.activate
def test_shop_caching_disabled():
    """Test that caching can be disabled."""
    # Mock shops list (needed for Shop initialization)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops.json",
        json=FIXTURES["shop_list_response"],
        status=200,
    )
    
    # Mock shop info
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123.json",
        json=FIXTURES["shop_info_response"],
        status=200,
    )
    
    # Mock products list (single page; one registration is reused for every
    # matching request, so it serves all get_products() calls in this test)
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/shop_123/products.json",
        json=FIXTURES["product_list_response"],
        status=200,
    )

    shop = Shop(shop_id="shop_123", api_key="test_api_key", enable_cache=False)
    
    # First call
    products1 = shop.get_products()
    call_count_1 = len([c for c in responses.calls if 'products.json' in c.request.url])
    
    # Second call - should NOT use cache
    products2 = shop.get_products()
    call_count_2 = len([c for c in responses.calls if 'products.json' in c.request.url])
    
    # With caching disabled, should make a new API call
    assert call_count_2 == call_count_1 + 1
