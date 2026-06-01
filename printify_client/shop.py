"""
Shop class - main entry point for the Printify Python library.

This module provides the Shop class which serves as the primary interface
for interacting with a Printify shop. It orchestrates all shop-related
operations including products, orders, and shipping calculations.
"""

import os
from typing import Optional, List

from printify_client.client import APIClient
from printify_client.cache import CacheManager
from printify_client.models.shop import ShopInfo
from printify_client.models.product import Product
from printify_client.models.order import Order, LineItem, Address
from printify_client.models.shipping import ShippingCost
from printify_client.services.product_service import ProductService
from printify_client.services.shipping_service import ShippingService
from printify_client.services.order_service import OrderService
from printify_client.exceptions import ValidationError, NotFoundError


class Shop:
    """
    Main interface for interacting with a Printify shop.
    
    This class provides a high-level API for all shop operations including
    product management, shipping calculations, and order creation. It handles
    initialization, authentication, and service orchestration.
    
    Args:
        shop_id: Printify shop ID (optional if shop_name provided)
        shop_name: Shop name to lookup ID (optional if shop_id provided)
        api_key: Printify API key (defaults to PRINTIFY_API_KEY env var)
        enable_cache: Enable response caching (default: True)
        cache_ttl: Cache time-to-live in seconds (default: 7200)
    
    Raises:
        ValidationError: If neither shop_id nor shop_name provided
        AuthenticationError: If API key is invalid or missing
        NotFoundError: If shop is not found
    
    Example:
        >>> # Initialize with shop ID
        >>> shop = Shop(shop_id="12345", api_key="your_api_key")
        >>> 
        >>> # Initialize with shop name
        >>> shop = Shop(shop_name="My Store", api_key="your_api_key")
        >>> 
        >>> # Use environment variable for API key
        >>> os.environ['PRINTIFY_API_KEY'] = 'your_api_key'
        >>> shop = Shop(shop_id="12345")
        >>> 
        >>> # Get products
        >>> products = shop.get_products()
    """

    def __init__(
        self,
        shop_id: Optional[str] = None,
        shop_name: Optional[str] = None,
        api_key: Optional[str] = None,
        enable_cache: bool = True,
        cache_ttl: int = 7200,
    ):
        """
        Initialize the Shop instance.
        
        Args:
            shop_id: Printify shop ID (optional if shop_name provided)
            shop_name: Shop name to lookup ID (optional if shop_id provided)
            api_key: Printify API key (defaults to PRINTIFY_API_KEY env var)
            enable_cache: Enable response caching (default: True)
            cache_ttl: Cache time-to-live in seconds (default: 7200)
        
        Raises:
            ValidationError: If neither shop_id nor shop_name provided
            AuthenticationError: If API key is invalid or missing
            NotFoundError: If shop is not found
        """
        # Validate that at least one shop identifier is provided
        if not shop_id and not shop_name:
            raise ValidationError(
                "Either shop_id or shop_name must be provided"
            )

        # Load API key from environment variable if not provided
        if api_key is None:
            api_key = os.environ.get('PRINTIFY_API_KEY')

        if not api_key:
            raise ValidationError(
                "API key must be provided either as parameter or via "
                "PRINTIFY_API_KEY environment variable"
            )

        # Initialize API client
        self.client = APIClient(api_key=api_key)

        # Initialize cache manager if enabled
        self.cache_manager: Optional[CacheManager] = None
        if enable_cache:
            self.cache_manager = CacheManager(ttl=cache_ttl)
        else:
            # Create a no-op cache manager
            self.cache_manager = CacheManager(ttl=0, max_size=0)

        # Resolve shop_id from shop_name if needed
        if shop_name and not shop_id:
            shop_id = self._resolve_shop_id(shop_name)

        self.shop_id = shop_id

        # Validate shop exists by fetching shop info
        self._shop_info = self.get_info()

        # Initialize services
        self.product_service = ProductService(
            client=self.client,
            shop_id=self.shop_id,
            cache_manager=self.cache_manager,
        )

        self.shipping_service = ShippingService(
            client=self.client,
            cache_manager=self.cache_manager,
        )

        self.order_service = OrderService(
            client=self.client,
            shop_id=self.shop_id,
        )

    def get_info(self) -> ShopInfo:
        """
        Retrieve shop information and metadata.
        
        Fetches details about the shop including ID, name, and sales channel.
        This method is called during initialization to validate shop access.
        
        Returns:
            ShopInfo object with shop details
        
        Raises:
            NotFoundError: If shop is not found
            AuthenticationError: If API key is invalid
            APIError: If API request fails
        
        Example:
            >>> shop = Shop(shop_id="12345", api_key="your_api_key")
            >>> info = shop.get_info()
            >>> print(f"Shop: {info.title}")
        """
        # Printify API doesn't have a single shop endpoint, so we fetch all shops
        # and find the one matching our shop_id
        endpoint = "/shops.json"
        data = self.client.get(endpoint)

        # API returns list of shops
        shops = data if isinstance(data, list) else data.get('data', [])

        # Find shop by ID
        for shop_data in shops:
            if str(shop_data.get('id')) == str(self.shop_id):
                return ShopInfo(
                    id=shop_data.get('id', self.shop_id),
                    title=shop_data.get('title', ''),
                    sales_channel=shop_data.get('sales_channel'),
                )

        # Shop not found
        raise NotFoundError("Shop", self.shop_id)

    def _resolve_shop_id(self, shop_name: str) -> str:
        """
        Lookup shop ID from shop name.
        
        Makes a GET request to /shops.json to list all shops accessible
        with the provided API key, then finds the shop matching the given name.
        
        Args:
            shop_name: Name of the shop to find
        
        Returns:
            Shop ID string
        
        Raises:
            NotFoundError: If shop name is not found
            AuthenticationError: If API key is invalid
            APIError: If API request fails
        
        Example:
            >>> shop_id = shop._resolve_shop_id("My Store")
        """
        endpoint = "/shops.json"
        data = self.client.get(endpoint)

        # API returns list of shops
        shops = data if isinstance(data, list) else data.get('data', [])

        # Find shop by name (case-insensitive)
        shop_name_lower = shop_name.lower()
        for shop_data in shops:
            if shop_data.get('title', '').lower() == shop_name_lower:
                return shop_data['id']

        # Shop not found
        raise NotFoundError("Shop", shop_name)

    def get_products(self, include_disabled: bool = False) -> List[Product]:
        """
        Retrieve all products from the shop.
        
        Fetches all products using concurrent pagination for improved performance.
        By default, filters out products without enabled variants.
        
        Args:
            include_disabled: If True, include products without enabled variants
        
        Returns:
            List of Product objects
        
        Example:
            >>> shop = Shop(shop_id="12345", api_key="your_api_key")
            >>> products = shop.get_products()
            >>> for product in products:
            ...     print(f"{product.title}: ${product.price_range[0]}")
        """
        return self.product_service.get_all_products(include_disabled=include_disabled)

    def get_product(self, product_id: str) -> Product:
        """
        Retrieve a single product by ID.
        
        Args:
            product_id: The product ID to retrieve
        
        Returns:
            Product object
        
        Raises:
            NotFoundError: If product is not found
        
        Example:
            >>> shop = Shop(shop_id="12345", api_key="your_api_key")
            >>> product = shop.get_product("prod_123")
            >>> print(f"Product: {product.title}")
        """
        return self.product_service.get_product_by_id(product_id)

    def filter_products(self, **filters) -> List[Product]:
        """
        Filter products by attributes.
        
        Filters products from the shop's catalog based on keyword arguments.
        Supports filtering by any product attribute.
        
        Args:
            **filters: Keyword arguments for filtering (e.g., title="Shirt", blueprint_id=3)
        
        Returns:
            List of Product objects matching the filters
        
        Example:
            >>> shop = Shop(shop_id="12345", api_key="your_api_key")
            >>> tshirts = shop.filter_products(blueprint_id=3)
            >>> custom_products = shop.filter_products(title="Custom Design")
        """
        return self.product_service.filter_products(**filters)

    def calculate_shipping(
        self,
        line_items: List[LineItem],
        address: Address,
    ) -> ShippingCost:
        """
        Calculate shipping cost for items and destination.
        
        Fetches shipping profiles and calculates total cost using first-item
        and additional-items pricing rules. Automatically retrieves product
        information needed for the calculation.
        
        Args:
            line_items: List of items to ship
            address: Destination address
        
        Returns:
            ShippingCost object with total cost and per-item breakdown
        
        Raises:
            NotFoundError: If a referenced product does not exist
            ShippingCalculationError: If shipping profile cannot be found
            ValidationError: If input is invalid

        Example:
            >>> shop = Shop(shop_id="12345", api_key="your_api_key")
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
            >>> print(f"Shipping cost: {shipping}")
        """
        # Fetch only the products referenced by the line items rather than the
        # entire catalog, keeping shipping calculation cheap for large shops.
        product_ids = {item.product_id for item in line_items}
        products = [
            self.get_product(product_id) for product_id in product_ids
        ]

        # Delegate to shipping service
        return self.shipping_service.calculate_cost(
            line_items=line_items,
            address=address,
            products=products,
        )

    def create_order(
        self,
        line_items: List[LineItem],
        shipping_address: Address,
        external_id: Optional[str] = None,
        label: Optional[str] = None,
        send_notification: bool = True,
    ) -> Order:
        """
        Create an order in Printify.
        
        Validates input, creates the order via the API, and returns
        the created order details.
        
        Args:
            line_items: List of items to include in the order
            shipping_address: Destination address for shipping
            external_id: Optional external order reference (e.g., from your system)
            label: Optional customer label or note
            send_notification: Whether to send order notification (default: True)
        
        Returns:
            Order object with the created order details
        
        Raises:
            ValidationError: If required fields are missing or invalid
            APIError: If the API request fails
            AuthenticationError: If API key is invalid
        
        Example:
            >>> shop = Shop(shop_id="12345", api_key="your_api_key")
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
            >>> order = shop.create_order(items, address, external_id="order_12345")
            >>> print(f"Order created: {order.id}")
        """
        return self.order_service.create_order(
            line_items=line_items,
            shipping_address=shipping_address,
            external_id=external_id,
            label=label,
            send_notification=send_notification,
        )

    def clear_cache(self) -> None:
        """
        Clear all cached data for this shop.
        
        Removes all cached products, shipping profiles, and other data.
        Useful when you need to force fresh data from the API.
        
        Example:
            >>> shop = Shop(shop_id="12345", api_key="your_api_key")
            >>> products = shop.get_products()  # Cached
            >>> shop.clear_cache()
            >>> products = shop.get_products()  # Fresh from API
        """
        if self.cache_manager:
            self.cache_manager.clear()
