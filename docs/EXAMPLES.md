# Printify Python Library - Examples

This document provides comprehensive examples for using the Printify Python library.

## Table of Contents

- [Basic Setup](#basic-setup)
- [Working with Products](#working-with-products)
- [Shipping Calculations](#shipping-calculations)
- [Order Management](#order-management)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)

## Basic Setup

### Initialize with Shop ID

```python
from printify_client import Shop

shop = Shop(
    shop_id="12345",
    api_key="your_api_key"
)
```

### Initialize with Shop Name

```python
from printify_client import Shop

# Library will automatically lookup the shop ID
shop = Shop(
    shop_name="My Awesome Store",
    api_key="your_api_key"
)
```

### Using Environment Variables

```python
import os
from printify_client import Shop

# Set API key in environment
os.environ['PRINTIFY_API_KEY'] = 'your_api_key_here'

# No need to pass api_key parameter
shop = Shop(shop_id="12345")
```

### Custom Configuration

```python
from printify_client import Shop

shop = Shop(
    shop_id="12345",
    api_key="your_api_key",
    enable_cache=True,      # Enable caching
    cache_ttl=3600         # Cache for 1 hour
)
```

## Working with Products

### Get All Products

```python
# Get all products with enabled variants
products = shop.get_products()

for product in products:
    print(f"Product: {product.title}")
    print(f"  ID: {product.id}")
    print(f"  Blueprint: {product.blueprint_id}")
    print(f"  Variants: {len(product.enabled_variants)}")
    print()
```

### Get Single Product

```python
# Get a specific product by ID
product = shop.get_product("prod_123")

print(f"Product: {product.title}")
print(f"Description: {product.description}")
print(f"Number of variants: {len(product.variants)}")
```

### Working with Variants

```python
product = shop.get_product("prod_123")

# Get all enabled variants
for variant in product.enabled_variants:
    print(f"{variant.title}: ${variant.price:.2f}")

# Get price range
min_price, max_price = product.price_range
print(f"Price range: ${min_price:.2f} - ${max_price:.2f}")

# Get specific variant
variant = product.get_variant(variant_id=456)
if variant:
    print(f"Variant: {variant.title}")
    print(f"Price: ${variant.price:.2f}")
    print(f"Enabled: {variant.is_enabled}")
```

### Working with Images

```python
product = shop.get_product("prod_123")

# Get default image
if product.default_image:
    print(f"Default image: {product.default_image.src}")

# Get all images
for image in product.images:
    print(f"Image URL: {image.src}")
    print(f"Position: {image.position}")
    print(f"Variant IDs: {image.variant_ids}")
    print(f"Is default: {image.is_default}")
    print()
```

### Filter Products

```python
# Filter by blueprint ID (product type)
# Blueprint 3 = T-shirts, 6 = Hoodies, etc.
tshirts = shop.filter_products(blueprint_id=3)
print(f"Found {len(tshirts)} t-shirts")

# Filter by print provider
provider_products = shop.filter_products(print_provider_id=5)

# Filter by title
custom_products = shop.filter_products(title="Custom Design")

# Combine with Python filtering
affordable_tshirts = [
    p for p in shop.filter_products(blueprint_id=3)
    if p.price_range[0] < 20
]
print(f"Found {len(affordable_tshirts)} affordable t-shirts")
```

### Include Disabled Products

```python
# Get all products including those without enabled variants
all_products = shop.get_products(include_disabled=True)

# Filter to find disabled products
disabled_products = [
    p for p in all_products
    if not p.enabled_variants
]
print(f"Found {len(disabled_products)} disabled products")
```

## Shipping Calculations

### Basic Shipping Calculation

```python
from printify_client import LineItem, Address

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
print(f"Total shipping cost: {shipping}")  # e.g., "5.99 USD"
```

### Shipping Cost Breakdown

```python
# Calculate shipping and view breakdown
shipping = shop.calculate_shipping(items, address)

print(f"Total: ${shipping.cost:.2f} {shipping.currency}")
print("\nBreakdown:")
for item in shipping.breakdown:
    print(f"  Product {item.product_id}, Variant {item.variant_id}")
    print(f"    Quantity: {item.quantity}")
    print(f"    Cost: ${item.cost:.2f}")
```

### Calculate Shipping to Multiple Destinations

```python
from printify_client import LineItem, Address, ShippingCalculationError

items = [LineItem(product_id="prod_123", variant_id=456, quantity=1)]

destinations = {
    "US": Address(
        first_name="John", last_name="Doe", email="john@example.com",
        country="US", region="CA", city="Los Angeles",
        zip_code="90001", address1="123 Main St"
    ),
    "UK": Address(
        first_name="Jane", last_name="Smith", email="jane@example.com",
        country="GB", region="England", city="London",
        zip_code="SW1A 1AA", address1="10 Downing St"
    ),
    "Canada": Address(
        first_name="Bob", last_name="Johnson", email="bob@example.com",
        country="CA", region="ON", city="Toronto",
        zip_code="M5H 2N2", address1="100 Queen St"
    ),
}

for country, address in destinations.items():
    try:
        shipping = shop.calculate_shipping(items, address)
        print(f"{country}: ${shipping.cost:.2f} {shipping.currency}")
    except ShippingCalculationError as e:
        print(f"{country}: Cannot calculate shipping - {e}")
```

### Compare Shipping Costs

```python
# Compare shipping costs for different quantities
product_id = "prod_123"
variant_id = 456

address = Address(
    first_name="John", last_name="Doe", email="john@example.com",
    country="US", region="CA", city="San Francisco",
    zip_code="94102", address1="123 Main St"
)

for quantity in [1, 2, 5, 10]:
    items = [LineItem(product_id=product_id, variant_id=variant_id, quantity=quantity)]
    shipping = shop.calculate_shipping(items, address)
    cost_per_item = shipping.cost / quantity
    print(f"Quantity {quantity}: ${shipping.cost:.2f} total (${cost_per_item:.2f} per item)")
```

## Order Management

### Create Basic Order

```python
from printify_client import LineItem, Address

# Create line items
items = [
    LineItem(product_id="prod_123", variant_id=456, quantity=2)
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
    address1="123 Main St",
    phone="+1-555-0123"  # Optional
)

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

### Create Order with Multiple Items

```python
# Create order with multiple products
items = [
    LineItem(product_id="prod_123", variant_id=456, quantity=2),
    LineItem(product_id="prod_789", variant_id=101, quantity=1),
    LineItem(product_id="prod_456", variant_id=789, quantity=3)
]

order = shop.create_order(
    line_items=items,
    shipping_address=address,
    external_id="order_67890"
)

print(f"Order {order.id} created with {len(order.line_items)} items")
```

### Batch Order Creation

```python
from printify_client import Shop, LineItem, Address, ValidationError, APIError

shop = Shop(shop_id="12345", api_key="your_api_key")

# List of orders to create
orders_data = [
    {
        "external_id": "order_001",
        "items": [LineItem(product_id="prod_123", variant_id=456, quantity=1)],
        "address": Address(
            first_name="John", last_name="Doe", email="john@example.com",
            country="US", region="CA", city="Los Angeles",
            zip_code="90001", address1="123 Main St"
        )
    },
    {
        "external_id": "order_002",
        "items": [LineItem(product_id="prod_789", variant_id=101, quantity=2)],
        "address": Address(
            first_name="Jane", last_name="Smith", email="jane@example.com",
            country="US", region="NY", city="New York",
            zip_code="10001", address1="456 Broadway"
        )
    },
    # ... more orders
]

# Process orders
successful_orders = []
failed_orders = []

for order_data in orders_data:
    try:
        order = shop.create_order(
            line_items=order_data["items"],
            shipping_address=order_data["address"],
            external_id=order_data["external_id"]
        )
        successful_orders.append(order)
        print(f"✓ Created order {order.id} for {order_data['external_id']}")
    except (ValidationError, APIError) as e:
        failed_orders.append({
            "external_id": order_data["external_id"],
            "error": str(e)
        })
        print(f"✗ Failed to create order {order_data['external_id']}: {e}")

print(f"\nSummary: {len(successful_orders)} successful, {len(failed_orders)} failed")
```

### Check Order Status

```python
# Create order
order = shop.create_order(
    line_items=items,
    shipping_address=address,
    external_id="order_12345"
)

# Check if order is pending
if order.is_pending:
    print("Order is pending processing")
else:
    print(f"Order status: {order.status}")

# Access order details
print(f"Order ID: {order.id}")
print(f"External ID: {order.external_id}")
print(f"Created: {order.created_at}")
print(f"Items: {len(order.line_items)}")
```

## Error Handling

### Handle All Exception Types

```python
from printify_client import (
    Shop,
    AuthenticationError,
    NotFoundError,
    APIError,
    ValidationError,
    ShippingCalculationError,
    TimeoutError,
    PrintifyError
)

try:
    shop = Shop(shop_id="12345", api_key="your_api_key")
    products = shop.get_products()
    
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    print("Please check your API key")
    
except NotFoundError as e:
    print(f"Resource not found: {e}")
    print(f"Resource type: {e.resource_type}")
    print(f"Identifier: {e.identifier}")
    
except ValidationError as e:
    print(f"Validation error: {e}")
    print("Please check your input parameters")
    
except TimeoutError as e:
    print(f"Request timed out: {e}")
    print("Please try again later")
    
except APIError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response: {e.response}")
    
except PrintifyError as e:
    # Catch any other Printify-specific errors
    print(f"Printify error: {e}")
    
except Exception as e:
    # Catch any unexpected errors
    print(f"Unexpected error: {e}")
```

### Retry on Failure

```python
import time
from printify_client import Shop, TimeoutError, APIError

def get_products_with_retry(shop, max_retries=3, delay=5):
    """Get products with automatic retry on failure."""
    for attempt in range(max_retries):
        try:
            return shop.get_products()
        except (TimeoutError, APIError) as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed: {e}")
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Failed after {max_retries} attempts")
                raise

# Use the retry function
shop = Shop(shop_id="12345", api_key="your_api_key")
products = get_products_with_retry(shop)
```

### Graceful Degradation

```python
from printify_client import Shop, ShippingCalculationError

shop = Shop(shop_id="12345", api_key="your_api_key")

# Try to calculate shipping, fall back to default if it fails
try:
    shipping = shop.calculate_shipping(items, address)
    shipping_cost = shipping.cost
except ShippingCalculationError:
    print("Could not calculate shipping, using default rate")
    shipping_cost = 5.99  # Default shipping cost

print(f"Shipping cost: ${shipping_cost:.2f}")
```

## Advanced Usage

### Using Cache Effectively

```python
from printify_client import Shop

# Initialize with caching enabled
shop = Shop(
    shop_id="12345",
    api_key="your_api_key",
    enable_cache=True,
    cache_ttl=3600  # 1 hour
)

# First call - fetches from API
print("Fetching products (API call)...")
products = shop.get_products()

# Second call - returns cached data
print("Fetching products again (from cache)...")
products = shop.get_products()  # No API call

# Clear cache when you need fresh data
shop.clear_cache()
print("Cache cleared")

# Next call will fetch from API again
products = shop.get_products()
```

### Disable Caching

```python
# Disable caching for real-time data
shop = Shop(
    shop_id="12345",
    api_key="your_api_key",
    enable_cache=False
)

# Every call will fetch fresh data from API
products = shop.get_products()
```

### Get Shop Information

```python
# Get detailed shop information
shop = Shop(shop_id="12345", api_key="your_api_key")
info = shop.get_info()

print(f"Shop ID: {info.id}")
print(f"Shop Name: {info.title}")
print(f"Sales Channel: {info.sales_channel}")
```

### Working with Decimal Prices

```python
from decimal import Decimal

product = shop.get_product("prod_123")

# Prices are returned as Decimal for precision
for variant in product.enabled_variants:
    price = variant.price  # Decimal type
    
    # Format for display
    print(f"{variant.title}: ${price:.2f}")
    
    # Perform calculations
    tax_rate = Decimal("0.08")  # 8% tax
    total = price * (1 + tax_rate)
    print(f"  With tax: ${total:.2f}")
```

### Concurrent Operations

```python
from concurrent.futures import ThreadPoolExecutor
from printify_client import Shop

shop = Shop(shop_id="12345", api_key="your_api_key")

# Get multiple products concurrently
product_ids = ["prod_123", "prod_456", "prod_789"]

with ThreadPoolExecutor(max_workers=3) as executor:
    products = list(executor.map(shop.get_product, product_ids))

for product in products:
    print(f"Product: {product.title}")
```

### Custom Address Validation

```python
from printify_client import Address, ValidationError

def create_validated_address(**kwargs):
    """Create an address with custom validation."""
    required_fields = ['first_name', 'last_name', 'email', 'country', 
                      'region', 'city', 'zip_code', 'address1']
    
    # Check required fields
    missing = [f for f in required_fields if not kwargs.get(f)]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")
    
    # Validate email format
    email = kwargs['email']
    if '@' not in email:
        raise ValidationError(f"Invalid email format: {email}")
    
    # Create address
    return Address(**kwargs)

# Use validated address
try:
    address = create_validated_address(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        country="US",
        region="CA",
        city="San Francisco",
        zip_code="94102",
        address1="123 Main St"
    )
except ValidationError as e:
    print(f"Address validation failed: {e}")
```

### Product Catalog Export

```python
import json
from printify_client import Shop

shop = Shop(shop_id="12345", api_key="your_api_key")

# Get all products
products = shop.get_products()

# Export to JSON
catalog = []
for product in products:
    catalog.append({
        "id": product.id,
        "title": product.title,
        "description": product.description,
        "blueprint_id": product.blueprint_id,
        "min_price": float(product.price_range[0]),
        "max_price": float(product.price_range[1]),
        "variants": [
            {
                "id": v.id,
                "title": v.title,
                "price": float(v.price),
                "enabled": v.is_enabled
            }
            for v in product.variants
        ],
        "default_image": product.default_image.src if product.default_image else None
    })

# Save to file
with open("product_catalog.json", "w") as f:
    json.dump(catalog, f, indent=2)

print(f"Exported {len(catalog)} products to product_catalog.json")
```

### Shipping Cost Analysis

```python
from printify_client import Shop, LineItem, Address
import statistics

shop = Shop(shop_id="12345", api_key="your_api_key")

# Analyze shipping costs across different regions
regions = [
    ("US-West", Address(first_name="Test", last_name="User", email="test@example.com",
                       country="US", region="CA", city="Los Angeles", 
                       zip_code="90001", address1="123 Main St")),
    ("US-East", Address(first_name="Test", last_name="User", email="test@example.com",
                       country="US", region="NY", city="New York",
                       zip_code="10001", address1="456 Broadway")),
    ("UK", Address(first_name="Test", last_name="User", email="test@example.com",
                  country="GB", region="England", city="London",
                  zip_code="SW1A 1AA", address1="10 Downing St")),
]

items = [LineItem(product_id="prod_123", variant_id=456, quantity=1)]

costs = []
for region_name, address in regions:
    try:
        shipping = shop.calculate_shipping(items, address)
        cost = float(shipping.cost)
        costs.append(cost)
        print(f"{region_name}: ${cost:.2f}")
    except Exception as e:
        print(f"{region_name}: Error - {e}")

if costs:
    print(f"\nAverage shipping cost: ${statistics.mean(costs):.2f}")
    print(f"Min: ${min(costs):.2f}, Max: ${max(costs):.2f}")
```

## Best Practices

### 1. Always Use Environment Variables for API Keys

```python
import os
from printify_client import Shop

# Good: Use environment variable
os.environ['PRINTIFY_API_KEY'] = 'your_api_key'
shop = Shop(shop_id="12345")

# Avoid: Hardcoding API keys in source code
# shop = Shop(shop_id="12345", api_key="hardcoded_key")  # Don't do this!
```

### 2. Enable Caching for Better Performance

```python
# Enable caching to reduce API calls
shop = Shop(
    shop_id="12345",
    api_key="your_api_key",
    enable_cache=True,
    cache_ttl=7200  # 2 hours
)
```

### 3. Handle Errors Gracefully

```python
from printify_client import Shop, PrintifyError

try:
    shop = Shop(shop_id="12345", api_key="your_api_key")
    products = shop.get_products()
except PrintifyError as e:
    # Log error and handle gracefully
    print(f"Error: {e}")
    products = []  # Use empty list as fallback
```

### 4. Validate Input Before API Calls

```python
from printify_client import LineItem, ValidationError

def create_line_item(product_id, variant_id, quantity):
    """Create a line item with validation."""
    if quantity < 1:
        raise ValidationError("Quantity must be at least 1")
    if quantity > 100:
        raise ValidationError("Quantity cannot exceed 100")
    
    return LineItem(
        product_id=product_id,
        variant_id=variant_id,
        quantity=quantity
    )
```

### 5. Use Type Hints

```python
from typing import List
from printify_client import Shop, Product, LineItem, Address, ShippingCost

def calculate_total_cost(
    shop: Shop,
    items: List[LineItem],
    address: Address
) -> float:
    """Calculate total cost including shipping."""
    # Get product prices
    total_product_cost = 0.0
    for item in items:
        product = shop.get_product(item.product_id)
        variant = product.get_variant(item.variant_id)
        if variant:
            total_product_cost += float(variant.price) * item.quantity
    
    # Get shipping cost
    shipping = shop.calculate_shipping(items, address)
    total_shipping_cost = float(shipping.cost)
    
    return total_product_cost + total_shipping_cost
```
