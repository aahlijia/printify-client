# Printify Python Library - Quick Reference

A quick reference guide for the Printify Python library.

## Installation

```bash
pip install printify-client
```

## Environment Setup

```bash
export PRINTIFY_API_KEY="your_api_key_here"
```

## Quick Start

```python
from printify_client import Shop, LineItem, Address

# Initialize shop
shop = Shop(shop_id="12345")

# Get products
products = shop.get_products()

# Calculate shipping
items = [LineItem(product_id="prod_123", variant_id=456, quantity=2)]
address = Address(
    first_name="John", last_name="Doe", email="john@example.com",
    country="US", region="CA", city="San Francisco",
    zip_code="94102", address1="123 Main St"
)
shipping = shop.calculate_shipping(items, address)

# Create order
order = shop.create_order(items, address, external_id="order_123")
```

## Common Operations

### Shop Initialization

```python
# By shop ID
shop = Shop(shop_id="12345", api_key="your_key")

# By shop name
shop = Shop(shop_name="My Store", api_key="your_key")

# With environment variable
shop = Shop(shop_id="12345")  # Uses PRINTIFY_API_KEY env var
```

### Products

```python
# Get all products
products = shop.get_products()

# Get single product
product = shop.get_product("prod_123")

# Filter products
tshirts = shop.filter_products(blueprint_id=3)

# Product properties
product.title
product.description
product.enabled_variants
product.price_range
product.default_image
```

### Shipping

```python
# Calculate shipping
shipping = shop.calculate_shipping(line_items, address)

# Access shipping details
shipping.cost          # Decimal
shipping.currency      # str (e.g., "USD")
shipping.breakdown     # List[ShippingBreakdown]
```

### Orders

```python
# Create order
order = shop.create_order(
    line_items=items,
    shipping_address=address,
    external_id="order_123",
    label="Customer Name",
    send_notification=True
)

# Order properties
order.id
order.status
order.created_at
order.is_pending
```

## Data Models

### LineItem

```python
LineItem(
    product_id="prod_123",
    variant_id=456,
    quantity=2
)
```

### Address

```python
Address(
    first_name="John",
    last_name="Doe",
    email="john@example.com",
    country="US",           # Required
    region="CA",            # Required
    city="San Francisco",   # Required
    zip_code="94102",       # Required
    address1="123 Main St", # Required
    address2="Apt 4",       # Optional
    phone="+1-555-0123"     # Optional
)
```

## Error Handling

```python
from printify_client import (
    AuthenticationError,
    NotFoundError,
    APIError,
    ValidationError,
    ShippingCalculationError,
    PrintifyTimeoutError
)

try:
    shop = Shop(shop_id="12345", api_key="your_key")
    products = shop.get_products()
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Resource not found")
except ValidationError:
    print("Invalid input")
except ShippingCalculationError:
    print("Cannot calculate shipping")
except PrintifyTimeoutError:
    print("Request timed out")
except APIError as e:
    print(f"API error: {e.status_code}")
```

## Configuration

```python
shop = Shop(
    shop_id="12345",
    api_key="your_key",
    enable_cache=True,      # Enable caching (default: True)
    cache_ttl=7200         # Cache TTL in seconds (default: 7200)
)

# Clear cache
shop.clear_cache()
```

## Common Patterns

### Get Product with Variants

```python
product = shop.get_product("prod_123")

for variant in product.enabled_variants:
    print(f"{variant.title}: ${variant.price:.2f}")

min_price, max_price = product.price_range
print(f"Price range: ${min_price:.2f} - ${max_price:.2f}")
```

### Calculate Total Cost

```python
# Product cost
total = 0
for item in items:
    product = shop.get_product(item.product_id)
    variant = product.get_variant(item.variant_id)
    total += variant.price * item.quantity

# Add shipping
shipping = shop.calculate_shipping(items, address)
total += shipping.cost

print(f"Total: ${total:.2f}")
```

### Batch Processing

```python
product_ids = ["prod_123", "prod_456", "prod_789"]

for product_id in product_ids:
    try:
        product = shop.get_product(product_id)
        print(f"✓ {product.title}")
    except NotFoundError:
        print(f"✗ Product {product_id} not found")
```

## Blueprint IDs (Product Types)

Common blueprint IDs for filtering:

- `3` - T-shirts
- `6` - Hoodies
- `9` - Mugs
- `17` - Posters
- `26` - Phone cases
- `71` - Canvas prints

```python
# Get all t-shirts
tshirts = shop.filter_products(blueprint_id=3)
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PRINTIFY_API_KEY` | Your Printify API key | Yes (if not passed to constructor) |

## API Rate Limits

The library automatically handles rate limiting with:
- Exponential backoff retry
- Maximum 3 retry attempts
- Retry on status codes: 429, 500, 502, 503, 504

## Caching

Default cache behavior:
- Enabled by default
- TTL: 7200 seconds (2 hours)
- Max size: 128 entries
- Thread-safe with LRU eviction

Cached operations:
- `get_products()`
- Shipping profiles

Not cached:
- `create_order()`
- `get_info()`

## Best Practices

1. **Use environment variables for API keys**
   ```python
   os.environ['PRINTIFY_API_KEY'] = 'your_key'
   shop = Shop(shop_id="12345")
   ```

2. **Enable caching for better performance**
   ```python
   shop = Shop(shop_id="12345", enable_cache=True, cache_ttl=7200)
   ```

3. **Handle errors gracefully**
   ```python
   try:
       products = shop.get_products()
   except PrintifyError as e:
       print(f"Error: {e}")
       products = []
   ```

4. **Validate input before API calls**
   ```python
   if not items:
       raise ValidationError("Line items cannot be empty")
   ```

5. **Use type hints**
   ```python
   from typing import List
   from printify_client import Product
   
   def process_products(products: List[Product]) -> None:
       ...
   ```

## Useful Links

- [Full Documentation](../README.md)
- [Comprehensive Examples](EXAMPLES.md)
- [Printify API Docs](https://developers.printify.com/)
