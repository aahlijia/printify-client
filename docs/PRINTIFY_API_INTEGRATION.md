# Printify REST API Integration Guide

## Overview

This document provides a comprehensive analysis of how the Printify REST API is integrated into the application, including endpoint usage, data structures, response handling, and performance optimizations.

## Table of Contents

1. [API Configuration](#api-configuration)
2. [Core Endpoints](#core-endpoints)
3. [Data Structures](#data-structures)
4. [Performance Optimizations](#performance-optimizations)
5. [Caching Strategy](#caching-strategy)
6. [Error Handling](#error-handling)
7. [Security Considerations](#security-considerations)

---

## API Configuration

### Base Configuration

The Printify API is configured in `config.py`:

```python
PRINTIFY_API_KEY = os.environ.get('PRINTIFY_API_KEY')
PRINTIFY_SHOP_ID = os.environ.get('PRINTIFY_SHOP_ID')
PRINTIFY_BASE_URL = 'https://api.printify.com/v1'
```

### Authentication

All API requests use Bearer token authentication:

```python
headers = {
    'Authorization': f'Bearer {PRINTIFY_API_KEY}',
    'Content-Type': 'application/json'
}
```

### HTTP Client

The application uses a custom `APIClient` class with:
- **Connection pooling**: 10 connections, 20 max pool size
- **Automatic retries**: Up to 3 retries with exponential backoff (0.3s, 0.6s, 1.2s)
- **Timeout**: 20 seconds default
- **SSL verification**: Enforced in production
- **Response size limits**: 10 MB maximum
- **Performance monitoring**: Logs all request durations

---

## Core Endpoints

### 1. Get All Products (Paginated)

**Endpoint**: `GET /shops/{shop_id}/products.json?page={page_num}`

**Purpose**: Fetch all products from the Printify catalog

**Implementation**: `app/services/product_service.py` - `_fetch_all_products_from_api()`

**Key Features**:
- **Concurrent pagination**: Fetches multiple pages simultaneously using ThreadPoolExecutor
- **Estimated max pages**: Starts with 4 pages, discovers actual count through 404 responses
- **Max workers**: 4 concurrent threads
- **Timeout**: 20 seconds per request

**Request Example**:
```python
url = f'{base_url}/shops/{shop_id}/products.json?page=1'
response = requests.get(url, headers=headers, timeout=20)
```

**Response Structure**:
```json
{
  "data": [
    {
      "id": "product_id_123",
      "title": "Cool T-Shirt",
      "description": "A cool t-shirt",
      "blueprint_id": 3,
      "print_provider_id": 99,
      "variants": [
        {
          "id": 12345,
          "title": "S / Black",
          "is_enabled": true,
          "price": 2999
        }
      ],
      "images": [
        {
          "src": "https://...",
          "variant_ids": [12345],
          "position": "front",
          "is_default": true
        }
      ]
    }
  ]
}
```

**Performance Optimization**:
- Concurrent fetching reduces total time from ~4 seconds (sequential) to ~1 second
- Automatic 404 detection prevents unnecessary requests
- Results cached for 2 hours (7200 seconds)

**Filtering**:
- Products without enabled variants are filtered out by default
- Uses `_has_enabled_variant()` to check `is_enabled` flag on variants

---

### 2. Get Single Product

**Endpoint**: `GET /shops/{shop_id}/products/{product_id}.json`

**Purpose**: Fetch detailed information for a specific product

**Implementation**: 
- `app/services/product_service.py` - `get_product_by_id()`
- `app/blueprints/shop.py` - `product_details()`

**Request Example**:
```python
url = f'{base_url}/shops/{shop_id}/products/{product_id}.json'
response = api_client.get(url, headers=headers)
```

**Response Structure**: Same as individual product in "Get All Products"

**Caching Behavior**:
1. First checks if product exists in cached "all products" list
2. If not found, makes direct API call
3. Individual product pages cached for 2 hours via Flask-Caching

---

### 3. Get Shipping Profile

**Endpoint**: `GET /catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/shipping.json`

**Purpose**: Calculate shipping costs for specific product types and destinations

**Implementation**: `app/services/shipping_calculator.py` - `_get_shipping_profile()`

**Request Parameters**:
```python
params = {
    'address_to[first_name]': 'John',
    'address_to[last_name]': 'Doe',
    'address_to[region]': 'CA',
    'address_to[address1]': '123 Main St',
    'address_to[city]': 'San Francisco',
    'address_to[zip]': '94102',
    'address_to[country]': 'US',
    'quantity': 1
}
```

**Response Structure**:
```json
{
  "profiles": [
    {
      "variant_ids": [12345, 67890],
      "first_item": {
        "cost": 499,
        "currency": "USD"
      },
      "additional_items": {
        "cost": 299,
        "currency": "USD"
      },
      "countries": ["US"]
    },
    {
      "variant_ids": [12345, 67890],
      "first_item": {
        "cost": 899,
        "currency": "USD"
      },
      "additional_items": {
        "cost": 499,
        "currency": "USD"
      },
      "countries": ["REST_OF_THE_WORLD"]
    }
  ]
}
```

**Cost Calculation Logic**:
```python
# For each product in cart:
if quantity == 1:
    cost = first_item_cost
else:
    cost = first_item_cost + (additional_item_cost * (quantity - 1))

# Total shipping = sum of all product costs
```

**Performance Optimization**:
- **Concurrent fetching**: Multiple shipping profiles fetched simultaneously
- **Max workers**: 5 concurrent threads
- **Caching**: 1-hour TTL cache (3600 seconds)
- **Cache key**: `{blueprint_id}:{print_provider_id}:{country}`
- **Timeout**: 10 seconds total for all shipping calculations

**Country Matching**:
1. First tries exact country match (e.g., "US")
2. Falls back to "REST_OF_THE_WORLD" if no exact match
3. Returns error if no profile found

---

### 4. Create Order

**Endpoint**: `POST /shops/{shop_id}/orders.json`

**Purpose**: Submit order to Printify for fulfillment after payment

**Implementation**: `app/blueprints/checkout.py` - `create_order()`

**Request Body**:
```json
{
  "external_id": "pi_stripe_payment_intent_id",
  "label": "John Doe",
  "line_items": [
    {
      "product_id": "product_123",
      "variant_id": 12345,
      "quantity": 2
    }
  ],
  "shipping_method": 1,
  "send_shipping_notification": true,
  "address_to": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "555-1234",
    "country": "US",
    "region": "CA",
    "address1": "123 Main St",
    "city": "San Francisco",
    "zip": "94102"
  }
}
```

**Response Structure**:
```json
{
  "id": "printify_order_id_abc123",
  "external_id": "pi_stripe_payment_intent_id",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Test Mode Behavior**:
- If Stripe payment is in test mode (`livemode == False`), **skips Printify order creation**
- Returns test order ID: `test_{payment_intent_id}`
- Allows full checkout testing without creating actual orders
- Logs: "TEST MODE: Skipping Printify order creation"

**Production Mode**:
- Creates actual order in Printify
- Returns real Printify order ID
- Printify handles fulfillment and shipping notifications

---

## Data Structures

### Product Object

```python
{
    'id': str,                    # Unique product ID
    'title': str,                 # Product name
    'description': str,           # Product description
    'blueprint_id': int,          # Product type (3 = t-shirt, etc.)
    'print_provider_id': int,     # Fulfillment provider
    'variants': [                 # Available variants
        {
            'id': int,            # Variant ID
            'title': str,         # "S / Black"
            'is_enabled': bool,   # Whether variant is available
            'price': int          # Price in cents
        }
    ],
    'images': [                   # Product images
        {
            'src': str,           # Image URL
            'variant_ids': [int], # Which variants use this image
            'position': str,      # "front", "back", etc.
            'is_default': bool    # Primary image
        }
    ]
}
```

### Shipping Profile Object

```python
{
    'first_item_cost': int,       # Cost for first item in cents
    'additional_item_cost': int   # Cost for each additional item in cents
}
```

### Line Item Object

```python
{
    'product_id': str,            # Printify product ID
    'variant_id': int,            # Specific variant ID
    'quantity': int               # Number of items
}
```

---

## Performance Optimizations

### 1. Two-Tier Caching Strategy

#### Product Data Cache (TTL Cache)
- **Location**: `ProductService._cache`
- **TTL**: 2 hours (7200 seconds)
- **Max size**: 128 entries
- **Thread-safe**: Uses `threading.RLock()`
- **LRU eviction**: Removes least recently used when full
- **Statistics tracking**: Hit rate, misses, evictions, expirations

**Cache Keys**:
- `all_products`: Products with enabled variants only
- `all_products_raw`: All products including disabled

**Benefits**:
- Reduces API calls from ~100/hour to ~1/hour
- Typical hit rate: >95% after warmup
- Memory usage: ~2-5 MB for 100 products

#### Page-Level Cache (Flask-Caching)
- **Type**: SimpleCache (in-memory)
- **TTL**: 2 hours (7200 seconds)
- **What's cached**: Rendered HTML pages

**Cached Routes**:
- `/` (home page)
- `/about`
- `/contact`
- `/shop/<category>` (category pages)
- `/product/<product_id>` (product details)

**Benefits**:
- Reduces page load time from ~500ms to ~50ms
- Eliminates template rendering overhead
- Reduces database/API queries

### 2. Concurrent API Requests

#### Product Fetching
```python
# Sequential (OLD): ~4 seconds for 4 pages
for page in range(1, 5):
    fetch_page(page)

# Concurrent (NEW): ~1 second for 4 pages
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(fetch_page, p) for p in range(1, 5)]
    results = [f.result() for f in as_completed(futures)]
```

**Performance Gain**: 75% reduction in fetch time

#### Shipping Profile Fetching
```python
# If cart has items from multiple blueprints/providers
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {
        executor.submit(get_profile, bp, pp): (bp, pp)
        for bp, pp in profiles_to_fetch
    }
```

**Performance Gain**: 60-80% reduction for multi-item carts

### 3. Connection Pooling

**Configuration**:
- Pool connections: 10
- Pool max size: 20
- Reuses TCP connections
- Reduces SSL handshake overhead

**Benefits**:
- Reduces request latency by ~50-100ms per request
- Handles concurrent requests efficiently

### 4. In-Memory Filtering

Instead of separate API calls for categories, products are filtered in-memory:

```python
def get_products_by_category(self, category: str):
    all_products = self.get_all_products()  # From cache
    
    # Filter in-memory
    return [p for p in all_products if category_matches(p['title'])]
```

**Benefits**:
- Zero additional API calls
- Instant response time (<10ms)
- Reduces Printify API load

### 5. Smart Cache Invalidation

**Manual Invalidation**:
```bash
# Clear all caches after product updates
curl -X POST http://localhost:5000/api/cache/clear?type=all
```

**Automatic Expiration**:
- TTL-based: Caches expire after 2 hours
- Periodic cleanup: Every 10 cache accesses
- Memory-efficient: Removes expired entries automatically

---

## Caching Strategy

### Cache Flow Diagram

```
User Request
    ↓
Flask-Caching (Page Cache)
    ↓ (miss)
ProductService.get_all_products()
    ↓
TTL Cache (Product Data)
    ↓ (miss)
Printify API (Concurrent Fetch)
    ↓
Cache & Return
```

### Cache Statistics

Monitor cache effectiveness:

```bash
curl http://localhost:5000/api/cache/stats
```

**Response**:
```json
{
  "product_cache": {
    "hits": 1250,
    "misses": 15,
    "hit_rate": 98.8,
    "current_size": 1,
    "total_size_bytes": 524288,
    "evictions": 0,
    "expirations": 2
  }
}
```

### Optimal TTL Values

| Cache Type | Current TTL | Recommended For |
|------------|-------------|-----------------|
| Product Data | 2 hours | Daily product updates |
| Page Cache | 2 hours | Daily product updates |
| Shipping Profiles | 1 hour | Stable shipping rates |

**Adjustment Guidelines**:
- **More frequent updates**: Reduce to 30-60 minutes
- **Less frequent updates**: Increase to 4-6 hours
- **Real-time updates**: Use webhook-based invalidation

---

## Error Handling

### API Request Errors

**Retry Strategy**:
- Max retries: 3
- Backoff: 0.3s, 0.6s, 1.2s (exponential)
- Retry on: 429, 500, 502, 503, 504 status codes

**Timeout Handling**:
- Default timeout: 20 seconds
- Shipping calculation timeout: 10 seconds
- Logs timeout duration and endpoint

**Error Responses**:
```python
try:
    response = api_client.get(url, headers=headers)
    response.raise_for_status()
except requests.exceptions.Timeout:
    logger.error(f"Request timed out after 20s")
    return fallback_value
except requests.exceptions.RequestException as e:
    logger.error(f"API request failed: {e}")
    return fallback_value
```

### Shipping Calculation Fallback

If shipping calculation fails:
1. Logs detailed error information
2. Returns `$5.00` fallback cost
3. Allows checkout to proceed
4. User sees: "Using estimated shipping cost"

**Fallback Triggers**:
- Product not found
- Missing blueprint/provider IDs
- Shipping profile API error
- Timeout exceeded
- Invalid cost calculation

### Order Creation Errors

**Payment Verification Failure**:
```json
{
  "success": false,
  "error": "Payment not completed"
}
```

**Printify API Failure**:
```json
{
  "success": false,
  "error": "Unable to create order",
  "detail": "API error details"
}
```

**User Experience**:
- Payment succeeded but order creation failed
- User receives payment intent ID for support
- Support team can manually create order in Printify

---

## Security Considerations

### 1. Authentication

- API keys stored in environment variables
- Never exposed to frontend
- Validated on application startup

### 2. Request Validation

**Size Limits**:
- Request body: 1-2 MB max
- Response body: 10 MB max
- Prevents memory exhaustion attacks

**Content-Type Validation**:
- Only accepts `application/json`
- Rejects unexpected content types

**Input Sanitization**:
- HTML sanitization on user inputs
- String length validation
- Address format validation

### 3. SSL/TLS

- SSL verification enforced in production
- Cannot be disabled in production environment
- Uses system certificate store

### 4. Rate Limiting

**Printify API Limits**:
- Handled by automatic retry with backoff
- 429 status code triggers retry
- Prevents API ban

**Application-Level**:
- Caching reduces API call frequency
- Connection pooling prevents connection exhaustion

### 5. Logging

**Security Logging**:
- Payment transactions logged
- Validation failures tracked
- API errors recorded
- No sensitive data in logs (PII redacted)

**Performance Logging**:
- Request durations tracked
- Slow API calls flagged (>5 seconds)
- Cache statistics monitored

---

## Best Practices

### 1. Always Use Caching

```python
# Good: Uses cached data
products = product_service.get_all_products()

# Bad: Direct API call every time
response = requests.get(f'{base_url}/products.json')
```

### 2. Handle Test Mode

```python
# Check if payment is test mode
is_test_mode = payment_intent.livemode == False

if is_test_mode:
    # Skip Printify order creation
    return test_order_response
else:
    # Create real order
    return create_printify_order()
```

### 3. Use Concurrent Fetching

```python
# For multiple independent API calls
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(fetch_data, item) for item in items]
    results = [f.result() for f in as_completed(futures)]
```

### 4. Implement Fallbacks

```python
try:
    shipping_cost = calculate_shipping(items, address)
except Exception as e:
    logger.error(f"Shipping calculation failed: {e}")
    shipping_cost = 5.00  # Fallback
```

### 5. Monitor Performance

```python
# Log slow operations
if duration > threshold:
    logger.warning(f"Slow operation: {duration:.2f}s")

# Track cache hit rates
stats = cache.get_stats()
logger.info(f"Cache hit rate: {stats['hit_rate']:.1f}%")
```

---

## Conclusion

The Printify API integration is optimized for:
- **Performance**: Concurrent requests, two-tier caching, connection pooling
- **Reliability**: Automatic retries, fallback mechanisms, error handling
- **Security**: SSL enforcement, input validation, rate limiting
- **Maintainability**: Centralized service classes, comprehensive logging

**Key Metrics**:
- API call reduction: ~99% (due to caching)
- Page load time: ~90% faster (cached pages)
- Shipping calculation: 60-80% faster (concurrent fetching)
- Cache hit rate: >95% after warmup

This architecture ensures a fast, reliable, and cost-effective integration with the Printify API.
