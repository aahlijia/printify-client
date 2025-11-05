# Printify Python Library

A Python library for interacting with the Printify REST API. This library provides an intuitive, easy-to-use interface for managing Printify shops, products, orders, and shipping calculations.

## Features

- 🛍️ **Shop Management**: Initialize shops by ID or name
- 📦 **Product Operations**: Retrieve and filter products with structured data models
- 🚚 **Shipping Calculations**: Calculate accurate shipping costs for any destination
- 📋 **Order Creation**: Programmatically create orders with validation
- 🔄 **Automatic Retries**: Built-in retry logic with exponential backoff
- 💾 **Optional Caching**: Reduce API calls with configurable TTL caching
- 🔒 **Type Safety**: Full type hints for better IDE support
- ⚡ **Concurrent Requests**: Parallel API calls for improved performance

## Installation

Install the library using pip:

```bash
pip install printify-python
```

For development:

```bash
pip install printify-python[dev]
```

## Quick Start

### Initialize a Shop

```python
from printify import Shop

# Using shop ID
shop = Shop(shop_id="12345", api_key="your_api_key")

# Using shop name (library will lookup the ID)
shop = Shop(shop_name="My Shop", api_key="your_api_key")

# Using environment variable for API key
import os
os.environ['PRINTIFY_API_KEY'] = 'your_api_key'
shop = Shop(shop_id="12345")
```

### Retrieve Products

```python
# Get all products
products = shop.get_products()

for product in products:
    print(f"{product.title}: ${product.price_range[0]:.2f} - ${product.price_range[1]:.2f}")
    print(f"  Variants: {len(product.enabled_variants)}")
    print(f"  Default image: {product.default_image.src if product.default_image else 'None'}")

# Get a single product
product = shop.get_product("product_123")
print(f"Product: {product.title}")

# Filter products
tshirts = shop.filter_products(blueprint_id=3)
```

### Calculate Shipping Costs

```python
from printify import LineItem, Address

# Create line items
items = [
    LineItem(product_id="prod_123", variant_id=456, quantity=2),
    LineItem(product_id="prod_789", variant_id=101, quantity=1)
]

# Create shipping address
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

# Calculate shipping
shipping = shop.calculate_shipping(items, address)
print(f"Shipping cost: {shipping}")  # e.g., "5.99 USD"

# View breakdown
for item in shipping.breakdown:
    print(f"  Product {item.product_id}: ${item.cost:.2f}")
```

### Create an Order

```python
from printify import LineItem, Address

# Create order
order = shop.create_order(
    line_items=items,
    shipping_address=address,
    external_id="order_12345",  # Your order ID
    label="John Doe",
    send_notification=True
)

print(f"Order created: {order.id}")
print(f"Status: {order.status}")
print(f"Created at: {order.created_at}")
```

### Error Handling

```python
from printify import (
    Shop,
    AuthenticationError,
    NotFoundError,
    APIError,
    ValidationError,
    ShippingCalculationError
)

try:
    shop = Shop(shop_id="12345", api_key="invalid_key")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")

try:
    product = shop.get_product("nonexistent_id")
except NotFoundError as e:
    print(f"Product not found: {e}")

try:
    shipping = shop.calculate_shipping(items, address)
except ShippingCalculationError as e:
    print(f"Shipping calculation failed: {e}")
```

## Configuration

### Environment Variables

```bash
export PRINTIFY_API_KEY="your_api_key_here"
export PRINTIFY_CACHE_TTL=7200
export PRINTIFY_CACHE_ENABLED=true
export PRINTIFY_TIMEOUT=20
export PRINTIFY_MAX_RETRIES=3
```

### Programmatic Configuration

```python
shop = Shop(
    shop_id="12345",
    api_key="your_key",
    enable_cache=True,      # Enable caching (default: True)
    cache_ttl=3600          # Cache TTL in seconds (default: 7200)
)

# Clear cache manually
shop.clear_cache()
```

## API Reference

### Shop Class

The main entry point for interacting with Printify.

**Methods:**
- `get_info()` - Retrieve shop information
- `get_products(include_disabled=False)` - Get all products
- `get_product(product_id)` - Get a single product by ID
- `filter_products(**filters)` - Filter products by attributes
- `calculate_shipping(line_items, address)` - Calculate shipping costs
- `create_order(line_items, shipping_address, ...)` - Create an order
- `clear_cache()` - Clear cached data

### Data Models

**Product** - Represents a Printify product
- Properties: `id`, `title`, `description`, `blueprint_id`, `print_provider_id`, `variants`, `images`
- Methods: `enabled_variants`, `default_image`, `price_range`, `get_variant()`

**Variant** - Represents a product variant
- Properties: `id`, `title`, `is_enabled`, `price`

**Order** - Represents a Printify order
- Properties: `id`, `external_id`, `status`, `created_at`, `line_items`, `shipping_address`
- Methods: `is_pending`

**LineItem** - Represents an order line item
- Properties: `product_id`, `variant_id`, `quantity`

**Address** - Represents a shipping address
- Properties: `first_name`, `last_name`, `email`, `country`, `region`, `city`, `zip_code`, `address1`, `address2`, `phone`

**ShippingCost** - Represents calculated shipping cost
- Properties: `cost`, `currency`, `breakdown`

## Requirements

- Python 3.8 or higher
- requests >= 2.31.0
- urllib3 >= 2.0.0
- python-dateutil >= 2.8.0

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/printify/printify-python.git
cd printify-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
# Format code
black printify tests

# Lint code
ruff check printify tests

# Type checking
mypy printify
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please use the [GitHub issue tracker](https://github.com/printify/printify-python/issues).

## Links

- [Printify API Documentation](https://developers.printify.com/)
- [GitHub Repository](https://github.com/printify/printify-python)
