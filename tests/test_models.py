"""Tests for data models."""

import json
from decimal import Decimal
from pathlib import Path

from printify.models.product import Product, Variant, Image
from printify.models.order import LineItem, Address, Order
from printify.models.shipping import ShippingCost, ShippingBreakdown
from printify.models import parse_product, parse_variant, parse_image


# Load test fixtures
fixtures_path = Path(__file__).parent / "fixtures" / "api_responses.json"
with open(fixtures_path) as f:
    FIXTURES = json.load(f)


def test_variant_price_conversion():
    """Test that variant prices are correctly converted from cents to Decimal."""
    variant_data = FIXTURES["product_response"]["variants"][0]
    variant = parse_variant(variant_data)
    
    assert isinstance(variant.price, Decimal)
    assert variant.price == Decimal("25.00")
    assert variant.id == 101
    assert variant.title == "Small / Black"
    assert variant.is_enabled is True


def test_variant_str_representation():
    """Test Variant string representation."""
    variant = Variant(
        id=101,
        title="Small / Black",
        is_enabled=True,
        price=Decimal("25.00")
    )
    
    assert str(variant) == "Small / Black - $25.00"


def test_product_parsing():
    """Test Product model parsing from API response."""
    product_data = FIXTURES["product_response"]
    product = parse_product(product_data)
    
    assert product.id == "test_product_123"
    assert product.title == "Test T-Shirt"
    assert product.description == "A comfortable test t-shirt"
    assert product.blueprint_id == 3
    assert product.print_provider_id == 5
    assert len(product.variants) == 3
    assert len(product.images) == 2


def test_product_enabled_variants():
    """Test Product.enabled_variants property."""
    product_data = FIXTURES["product_response"]
    product = parse_product(product_data)
    
    enabled = product.enabled_variants
    assert len(enabled) == 2
    assert all(v.is_enabled for v in enabled)
    assert enabled[0].id == 101
    assert enabled[1].id == 102


def test_product_default_image():
    """Test Product.default_image property."""
    product_data = FIXTURES["product_response"]
    product = parse_product(product_data)
    
    default_img = product.default_image
    assert default_img is not None
    assert default_img.is_default is True
    assert default_img.position == "front"


def test_product_price_range():
    """Test Product.price_range property."""
    product_data = FIXTURES["product_response"]
    product = parse_product(product_data)
    
    min_price, max_price = product.price_range
    assert min_price == Decimal("25.00")
    assert max_price == Decimal("27.00")


def test_product_price_range_no_enabled_variants():
    """Test Product.price_range when no variants are enabled."""
    product = Product(
        id="test",
        title="Test",
        description="Test",
        blueprint_id=1,
        print_provider_id=1,
        variants=[
            Variant(id=1, title="Disabled", is_enabled=False, price=Decimal("10.00"))
        ],
        images=[]
    )
    
    min_price, max_price = product.price_range
    assert min_price == Decimal("0")
    assert max_price == Decimal("0")


def test_product_get_variant():
    """Test Product.get_variant method."""
    product_data = FIXTURES["product_response"]
    product = parse_product(product_data)
    
    variant = product.get_variant(102)
    assert variant is not None
    assert variant.id == 102
    assert variant.title == "Medium / Black"
    
    # Test non-existent variant
    assert product.get_variant(999) is None


def test_line_item_to_dict():
    """Test LineItem.to_dict() method."""
    line_item = LineItem(
        product_id="prod_123",
        variant_id=456,
        quantity=2
    )
    
    result = line_item.to_dict()
    assert result == {
        "product_id": "prod_123",
        "variant_id": 456,
        "quantity": 2
    }


def test_address_to_dict_with_optional_fields():
    """Test Address.to_dict() with all fields."""
    address = Address(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        country="US",
        region="CA",
        city="San Francisco",
        zip_code="94102",
        address1="123 Main St",
        address2="Apt 4B",
        phone="+1234567890"
    )
    
    result = address.to_dict()
    assert result["first_name"] == "John"
    assert result["last_name"] == "Doe"
    assert result["email"] == "john@example.com"
    assert result["country"] == "US"
    assert result["region"] == "CA"
    assert result["city"] == "San Francisco"
    assert result["zip"] == "94102"
    assert result["address1"] == "123 Main St"
    assert result["address2"] == "Apt 4B"
    assert result["phone"] == "+1234567890"


def test_address_to_dict_without_optional_fields():
    """Test Address.to_dict() without optional fields."""
    address = Address(
        first_name="Jane",
        last_name="Smith",
        email="jane@example.com",
        country="UK",
        region="London",
        city="London",
        zip_code="SW1A 1AA",
        address1="10 Downing St"
    )
    
    result = address.to_dict()
    assert "address2" not in result
    assert "phone" not in result
    assert result["first_name"] == "Jane"


def test_shipping_cost_str_representation():
    """Test ShippingCost string representation."""
    shipping_cost = ShippingCost(
        cost=Decimal("12.50"),
        currency="USD",
        breakdown=[]
    )
    
    assert str(shipping_cost) == "12.50 USD"


def test_shipping_breakdown_creation():
    """Test ShippingBreakdown model creation."""
    breakdown = ShippingBreakdown(
        product_id="prod_123",
        variant_id=456,
        quantity=2,
        cost=Decimal("8.50")
    )
    
    assert breakdown.product_id == "prod_123"
    assert breakdown.variant_id == 456
    assert breakdown.quantity == 2
    assert breakdown.cost == Decimal("8.50")
