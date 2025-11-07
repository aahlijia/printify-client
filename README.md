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
pip install printify-client
```

For development:

```bash
pip install printify-client[dev]
```

## Quick Start

### Initialize a Shop

```python
from printify_client import Shop

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
print(f"Shipping cost: {shipping}")  # e.g., "5.99 USD"

# View breakdown
for item in shipping.breakdown:
    print(f"  Product {item.product_id}: ${item.cost:.2f}")
```

### Create an Order

```python
from printify_client import LineItem, Address

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

The library provides specific exception types for different error scenarios:

```python
from printify_client import (
    Shop,
    AuthenticationError,
    NotFoundError,
    APIError,
    ValidationError,
    ShippingCalculationError,
    TimeoutError
)

# Handle authentication errors
try:
    shop = Shop(shop_id="12345", api_key="invalid_key")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Check your API key and ensure it's valid

# Handle not found errors
try:
    product = shop.get_product("nonexistent_id")
except NotFoundError as e:
    print(f"Resource not found: {e}")
    print(f"Resource type: {e.resource_type}")
    print(f"Identifier: {e.identifier}")

# Handle shipping calculation errors
try:
    shipping = shop.calculate_shipping(items, address)
except ShippingCalculationError as e:
    print(f"Shipping calculation failed: {e}")
    # Check that products support shipping to the destination

# Handle API errors
try:
    order = shop.create_order(items, address)
except APIError as e:
    print(f"API error occurred: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response: {e.response}")

# Handle timeout errors
try:
    products = shop.get_products()
except TimeoutError as e:
    print(f"Request timed out: {e}")
    # Consider increasing timeout or retrying

# Handle validation errors
try:
    shop = Shop()  # Missing required parameters
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Advanced Examples

### Working with Product Variants

```python
# Get a product and work with its variants
product = shop.get_product("prod_123")

# Get all enabled variants
for variant in product.enabled_variants:
    print(f"{variant.title}: ${variant.price:.2f}")

# Get price range
min_price, max_price = product.price_range
print(f"Price range: ${min_price:.2f} - ${max_price:.2f}")

# Get a specific variant
variant = product.get_variant(variant_id=456)
if variant:
    print(f"Found variant: {variant.title}")

# Get default image
if product.default_image:
    print(f"Default image URL: {product.default_image.src}")
```

### Filtering Products

```python
# Filter by blueprint ID (product type)
tshirts = shop.filter_products(blueprint_id=3)
hoodies = shop.filter_products(blueprint_id=6)

# Filter by print provider
products_by_provider = shop.filter_products(print_provider_id=5)

# Filter by title (partial match)
custom_products = shop.filter_products(title="Custom")

# Combine with Python filtering for complex queries
affordable_tshirts = [
    p for p in shop.filter_products(blueprint_id=3)
    if p.price_range[0] < 20
]
```

### Batch Order Processing

```python
from printify_client import Shop, LineItem, Address

shop = Shop(shop_id="12345", api_key="your_api_key")

# Process multiple orders
orders_to_create = [
    {
        "items": [LineItem(product_id="prod_123", variant_id=456, quantity=1)],
        "address": Address(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            country="US",
            region="CA",
            city="San Francisco",
            zip_code="94102",
            address1="123 Main St"
        ),
        "external_id": "order_001"
    },
    # ... more orders
]

created_orders = []
for order_data in orders_to_create:
    try:
        order = shop.create_order(
            line_items=order_data["items"],
            shipping_address=order_data["address"],
            external_id=order_data["external_id"]
        )
        created_orders.append(order)
        print(f"Created order {order.id} for {order_data['external_id']}")
    except Exception as e:
        print(f"Failed to create order {order_data['external_id']}: {e}")
```

### Calculating Shipping for Multiple Destinations

```python
# Calculate shipping to different countries
destinations = [
    Address(first_name="John", last_name="Doe", email="john@example.com",
            country="US", region="CA", city="Los Angeles", 
            zip_code="90001", address1="123 Main St"),
    Address(first_name="Jane", last_name="Smith", email="jane@example.com",
            country="GB", region="England", city="London",
            zip_code="SW1A 1AA", address1="10 Downing St"),
    Address(first_name="Bob", last_name="Johnson", email="bob@example.com",
            country="CA", region="ON", city="Toronto",
            zip_code="M5H 2N2", address1="100 Queen St"),
]

items = [LineItem(product_id="prod_123", variant_id=456, quantity=2)]

for address in destinations:
    try:
        shipping = shop.calculate_shipping(items, address)
        print(f"Shipping to {address.country}: {shipping}")
        
        # View per-item breakdown
        for item in shipping.breakdown:
            print(f"  Item {item.product_id}: ${item.cost:.2f}")
    except ShippingCalculationError as e:
        print(f"Cannot ship to {address.country}: {e}")
```

### Using Cache Effectively

```python
# Initialize with custom cache settings
shop = Shop(
    shop_id="12345",
    api_key="your_api_key",
    enable_cache=True,
    cache_ttl=3600  # 1 hour
)

# First call - fetches from API
products = shop.get_products()  # API call made

# Second call - returns cached data
products = shop.get_products()  # No API call, returns cached data

# Clear cache when you need fresh data
shop.clear_cache()
products = shop.get_products()  # API call made again

# Disable caching entirely
shop_no_cache = Shop(
    shop_id="12345",
    api_key="your_api_key",
    enable_cache=False
)
```

### Shop Information

```python
# Get shop details
shop = Shop(shop_id="12345", api_key="your_api_key")
info = shop.get_info()

print(f"Shop ID: {info.id}")
print(f"Shop Name: {info.title}")
print(f"Sales Channel: {info.sales_channel}")
```

## Configuration

### Environment Variables

The library supports configuration through environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PRINTIFY_API_KEY` | Your Printify API key | None | Yes (if not provided to constructor) |

**Setting environment variables:**

```bash
# Linux/macOS
export PRINTIFY_API_KEY="your_api_key_here"

# Windows (Command Prompt)
set PRINTIFY_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:PRINTIFY_API_KEY="your_api_key_here"

# Python
import os
os.environ['PRINTIFY_API_KEY'] = 'your_api_key_here'
```

**Getting your API key:**

1. Log in to your Printify account
2. Go to **Connections** > **API**
3. Generate a new API token
4. Copy the token and use it as your `PRINTIFY_API_KEY`

### Programmatic Configuration

You can configure the library when creating a Shop instance:

```python
shop = Shop(
    shop_id="12345",
    api_key="your_key",      # Override environment variable
    enable_cache=True,       # Enable caching (default: True)
    cache_ttl=3600          # Cache TTL in seconds (default: 7200)
)

# Clear cache manually when needed
shop.clear_cache()
```

**Configuration options:**

- `enable_cache` (bool): Enable/disable response caching. Caching improves performance by reducing API calls.
- `cache_ttl` (int): Time-to-live for cached data in seconds. Default is 7200 (2 hours).

## Troubleshooting

### Common Issues

#### Authentication Errors

**Problem:** `AuthenticationError: Invalid API key`

**Solutions:**
- Verify your API key is correct
- Check that the API key hasn't expired
- Ensure the API key has the necessary permissions
- Make sure there are no extra spaces or characters in the key

```python
# Test your API key
try:
    shop = Shop(shop_id="12345", api_key="your_api_key")
    info = shop.get_info()
    print(f"Successfully connected to shop: {info.title}")
except AuthenticationError:
    print("API key is invalid or expired")
```

#### Shop Not Found

**Problem:** `NotFoundError: Shop not found`

**Solutions:**
- Verify the shop ID is correct
- Check that the shop name matches exactly (case-insensitive)
- Ensure your API key has access to the shop

```python
# List all accessible shops
from printify_client.client import APIClient

client = APIClient(api_key="your_api_key")
shops = client.get("/shops.json")
for shop in shops:
    print(f"Shop ID: {shop['id']}, Name: {shop['title']}")
```

#### Shipping Calculation Errors

**Problem:** `ShippingCalculationError: No shipping profile found`

**Solutions:**
- Verify the product supports shipping to the destination country
- Check that the variant ID is correct and enabled
- Ensure the print provider ships to the destination

```python
# Check if product ships to a country
product = shop.get_product("prod_123")
print(f"Product: {product.title}")
print(f"Blueprint ID: {product.blueprint_id}")
print(f"Print Provider: {product.print_provider_id}")

# Try calculating shipping with error handling
try:
    shipping = shop.calculate_shipping(items, address)
    print(f"Shipping: {shipping}")
except ShippingCalculationError as e:
    print(f"Cannot calculate shipping: {e}")
    print("This product may not ship to the specified destination")
```

#### Timeout Errors

**Problem:** `TimeoutError: Request timed out`

**Solutions:**
- Check your internet connection
- The Printify API may be experiencing issues
- Try again after a short delay

```python
import time

max_attempts = 3
for attempt in range(max_attempts):
    try:
        products = shop.get_products()
        break
    except TimeoutError:
        if attempt < max_attempts - 1:
            print(f"Timeout, retrying in 5 seconds... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(5)
        else:
            print("Failed after multiple attempts")
            raise
```

#### Rate Limiting

The library automatically handles rate limiting with exponential backoff. If you're still experiencing rate limit issues:

- Reduce the frequency of API calls
- Enable caching to minimize redundant requests
- Batch operations when possible

```python
# Enable caching to reduce API calls
shop = Shop(
    shop_id="12345",
    api_key="your_api_key",
    enable_cache=True,
    cache_ttl=7200  # Cache for 2 hours
)
```

### Debug Mode

To see detailed information about API requests and responses, you can enable logging:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Now all API requests will be logged
shop = Shop(shop_id="12345", api_key="your_api_key")
products = shop.get_products()
```

## API Reference

### Shop Class

The main entry point for interacting with Printify. All operations start with creating a Shop instance.

#### Constructor

```python
Shop(
    shop_id: Optional[str] = None,
    shop_name: Optional[str] = None,
    api_key: Optional[str] = None,
    enable_cache: bool = True,
    cache_ttl: int = 7200
)
```

**Parameters:**
- `shop_id` (str, optional): Printify shop ID
- `shop_name` (str, optional): Shop name to lookup ID (alternative to shop_id)
- `api_key` (str, optional): Printify API key (defaults to `PRINTIFY_API_KEY` env var)
- `enable_cache` (bool): Enable response caching (default: True)
- `cache_ttl` (int): Cache time-to-live in seconds (default: 7200)

**Raises:**
- `ValidationError`: If neither shop_id nor shop_name provided, or if API key is missing
- `AuthenticationError`: If API key is invalid
- `NotFoundError`: If shop is not found

#### Methods

##### `get_info() -> ShopInfo`
Retrieve shop information and metadata.

**Returns:** `ShopInfo` object with shop details

**Raises:** `NotFoundError`, `AuthenticationError`, `APIError`

##### `get_products(include_disabled: bool = False) -> List[Product]`
Retrieve all products from the shop.

**Parameters:**
- `include_disabled` (bool): If True, include products without enabled variants

**Returns:** List of `Product` objects

##### `get_product(product_id: str) -> Product`
Retrieve a single product by ID.

**Parameters:**
- `product_id` (str): The product ID to retrieve

**Returns:** `Product` object

**Raises:** `NotFoundError` if product doesn't exist

##### `filter_products(**filters) -> List[Product]`
Filter products by attributes.

**Parameters:**
- `**filters`: Keyword arguments for filtering (e.g., `title="Shirt"`, `blueprint_id=3`)

**Returns:** List of `Product` objects matching the filters

##### `calculate_shipping(line_items: List[LineItem], address: Address) -> ShippingCost`
Calculate shipping cost for items and destination.

**Parameters:**
- `line_items` (List[LineItem]): List of items to ship
- `address` (Address): Destination address

**Returns:** `ShippingCost` object with total cost and breakdown

**Raises:** `ShippingCalculationError`, `ValidationError`

##### `create_order(line_items: List[LineItem], shipping_address: Address, external_id: Optional[str] = None, label: Optional[str] = None, send_notification: bool = True) -> Order`
Create an order in Printify.

**Parameters:**
- `line_items` (List[LineItem]): List of items to include in the order
- `shipping_address` (Address): Destination address for shipping
- `external_id` (str, optional): External order reference
- `label` (str, optional): Customer label or note
- `send_notification` (bool): Whether to send order notification (default: True)

**Returns:** `Order` object with created order details

**Raises:** `ValidationError`, `APIError`, `AuthenticationError`

##### `clear_cache() -> None`
Clear all cached data for this shop.

### Data Models

#### Product

Represents a Printify product with all its variants and images.

**Attributes:**
- `id` (str): Product ID
- `title` (str): Product title
- `description` (str): Product description
- `blueprint_id` (int): Blueprint ID (product type)
- `print_provider_id` (int): Print provider ID
- `variants` (List[Variant]): List of product variants
- `images` (List[Image]): List of product images

**Properties:**
- `enabled_variants` (List[Variant]): Returns only enabled variants
- `default_image` (Optional[Image]): Returns the default product image
- `price_range` (Tuple[Decimal, Decimal]): Returns (min_price, max_price) for enabled variants

**Methods:**
- `get_variant(variant_id: int) -> Optional[Variant]`: Get variant by ID

#### Variant

Represents a product variant (size/color combination).

**Attributes:**
- `id` (int): Variant ID
- `title` (str): Variant title (e.g., "Small / Black")
- `is_enabled` (bool): Whether variant is available
- `price` (Decimal): Variant price in decimal format

#### Image

Represents a product image.

**Attributes:**
- `src` (str): Image URL
- `variant_ids` (List[int]): List of variant IDs this image applies to
- `position` (str): Image position
- `is_default` (bool): Whether this is the default image

#### Order

Represents a Printify order.

**Attributes:**
- `id` (str): Order ID
- `external_id` (Optional[str]): External order reference
- `status` (str): Order status
- `created_at` (datetime): Order creation timestamp
- `line_items` (List[LineItem]): List of order items
- `shipping_address` (Address): Shipping address

**Properties:**
- `is_pending` (bool): Returns True if order status is 'pending'

#### LineItem

Represents an item in an order or cart.

**Attributes:**
- `product_id` (str): Product ID
- `variant_id` (int): Variant ID
- `quantity` (int): Quantity

**Methods:**
- `to_dict() -> Dict`: Convert to API request format

#### Address

Represents a shipping address.

**Attributes:**
- `first_name` (str): First name
- `last_name` (str): Last name
- `email` (str): Email address
- `country` (str): Country code (e.g., "US")
- `region` (str): State/region
- `city` (str): City
- `zip_code` (str): Postal/ZIP code
- `address1` (str): Address line 1
- `address2` (Optional[str]): Address line 2
- `phone` (Optional[str]): Phone number

**Methods:**
- `to_dict() -> Dict`: Convert to API request format

#### ShippingCost

Represents calculated shipping cost.

**Attributes:**
- `cost` (Decimal): Total shipping cost
- `currency` (str): Currency code (e.g., "USD")
- `breakdown` (List[ShippingBreakdown]): Per-item cost breakdown

#### ShippingBreakdown

Shipping cost breakdown for a single product.

**Attributes:**
- `product_id` (str): Product ID
- `variant_id` (int): Variant ID
- `quantity` (int): Quantity
- `cost` (Decimal): Shipping cost for this item

#### ShopInfo

Represents shop information.

**Attributes:**
- `id` (str): Shop ID
- `title` (str): Shop name
- `sales_channel` (Optional[str]): Sales channel information

### Exceptions

All exceptions inherit from `PrintifyError` base class.

#### `PrintifyError`
Base exception for all Printify library errors.

#### `AuthenticationError`
Raised when API key is invalid or missing.

#### `NotFoundError`
Raised when a resource is not found (404).

**Attributes:**
- `resource_type` (str): Type of resource not found
- `identifier` (str): Identifier used in lookup

#### `APIError`
Raised when API returns an error response.

**Attributes:**
- `status_code` (int): HTTP status code
- `message` (str): Error message
- `response` (Optional[Dict]): Full API response

#### `ValidationError`
Raised when input validation fails.

#### `ShippingCalculationError`
Raised when shipping cost calculation fails.

#### `TimeoutError`
Raised when API request times out.

## Requirements

- Python 3.8 or higher
- requests >= 2.31.0
- urllib3 >= 2.0.0
- python-dateutil >= 2.8.0

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/printify/printify-client.git
cd printify-client

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

For issues and questions, please use the [GitHub issue tracker](https://github.com/printify/printify-client/issues).

## Documentation

- [Quick Reference Guide](docs/QUICK_REFERENCE.md) - Quick reference for common operations
- [Comprehensive Examples](docs/EXAMPLES.md) - Detailed usage examples and patterns
- [API Integration Guide](docs/PRINTIFY_API_INTEGRATION.md) - Printify API integration details

## Links

- [Printify API Documentation](https://developers.printify.com/)
- [GitHub Repository](https://github.com/printify/printify-client)
