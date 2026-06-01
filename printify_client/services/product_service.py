"""
Product service for managing Printify products.

This module provides the ProductService class which handles all product-related
operations including fetching, filtering, and caching product data.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from printify_client.client import APIClient
from printify_client.cache import CacheManager
from printify_client.models import Product, parse_product
from printify_client.exceptions import NotFoundError


class ProductService:
    """
    Handles product-related operations.
    
    This service manages product retrieval, filtering, and caching.
    It uses concurrent pagination to efficiently fetch large product catalogs
    and provides filtering capabilities for product searches.
    
    Args:
        client: APIClient instance for making API requests
        shop_id: Printify shop ID
        cache_manager: CacheManager instance for caching responses
    
    Example:
        >>> service = ProductService(client, "12345", cache_manager)
        >>> products = service.get_all_products()
        >>> product = service.get_product_by_id("prod_123")
    """
    
    def __init__(self, client: APIClient, shop_id: str, cache_manager: CacheManager):
        """
        Initialize the product service.
        
        Args:
            client: APIClient instance for making API requests
            shop_id: Printify shop ID
            cache_manager: CacheManager instance for caching responses
        """
        self.client = client
        self.shop_id = shop_id
        self.cache = cache_manager
    
    def get_all_products(self, include_disabled: bool = False) -> List[Product]:
        """
        Fetch all products with concurrent pagination.
        
        Uses ThreadPoolExecutor to fetch multiple pages simultaneously for
        improved performance. Caches results based on include_disabled flag.
        Products without enabled variants are filtered out by default.
        
        Args:
            include_disabled: If True, include products without enabled variants
        
        Returns:
            List of Product objects
        
        Example:
            >>> products = service.get_all_products()
            >>> all_products = service.get_all_products(include_disabled=True)
        """
        cache_key = f"products_{self.shop_id}_{include_disabled}"
        
        # Check cache first
        if (cached := self.cache.get(cache_key)) is not None:
            return cached
        
        # Fetch products with concurrent pagination
        products = self._fetch_pages_concurrently()
        
        # Filter out products without enabled variants unless explicitly requested
        if not include_disabled:
            products = [p for p in products if p.enabled_variants]
        
        # Cache the results
        self.cache.set(cache_key, products)
        
        return products
    
    def get_product_by_id(self, product_id: str) -> Product:
        """
        Fetch single product by ID.
        
        Args:
            product_id: The product ID to retrieve
        
        Returns:
            Product object
        
        Raises:
            NotFoundError: If product is not found
        
        Example:
            >>> product = service.get_product_by_id("prod_123")
        """
        cache_key = f"product_{self.shop_id}_{product_id}"
        
        # Check cache first
        if (cached := self.cache.get(cache_key)) is not None:
            return cached
        
        # Fetch from API
        endpoint = f"/shops/{self.shop_id}/products/{product_id}.json"
        data = self.client.get(endpoint)
        
        # Parse and cache
        product = self._parse_product(data)
        self.cache.set(cache_key, product)
        
        return product
    
    def filter_products(self, **filters) -> List[Product]:
        """
        Filter products by attributes.
        
        Filters products from the cached/fetched product list based on
        keyword arguments. Supports filtering by any product attribute.
        
        Args:
            **filters: Keyword arguments for filtering (e.g., title="Shirt", blueprint_id=3)
        
        Returns:
            List of Product objects matching the filters
        
        Example:
            >>> products = service.filter_products(blueprint_id=3)
            >>> products = service.filter_products(title="T-Shirt")
        """
        # Get all products (this will use cache if available)
        products = self.get_all_products()
        
        # Apply filters
        filtered = products
        for key, value in filters.items():
            filtered = [
                p for p in filtered
                if hasattr(p, key) and getattr(p, key) == value
            ]
        
        return filtered
    
    def _fetch_pages_concurrently(self) -> List[Product]:
        """
        Fetch all product pages using Printify's pagination metadata.

        Fetches the first page to read the ``last_page`` count, then fetches
        any remaining pages concurrently in a single wave (4 workers).

        Returns:
            List of all Product objects from all pages
        """
        first_data = self._fetch_page_data(1)
        products = [
            self._parse_product(p) for p in first_data.get('data', [])
        ]
        if not products:
            return []

        last_page = first_data.get('last_page', 1)
        if last_page <= 1:
            return products

        # Fetch the remaining pages concurrently in a single wave.
        results: Dict[int, List[Product]] = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_page = {
                executor.submit(self._fetch_page, page): page
                for page in range(2, last_page + 1)
            }
            for future in as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    results[page] = future.result()
                except NotFoundError:
                    # Page vanished between the metadata read and the fetch;
                    # treat it as empty. Other errors propagate.
                    results[page] = []

        for page in sorted(results):
            products.extend(results[page])

        return products

    def _fetch_page_data(self, page: int) -> Dict[str, Any]:
        """
        Fetch the raw API response for a single page of products.

        Args:
            page: Page number to fetch (1-indexed)

        Returns:
            Raw API response dictionary, including pagination metadata

        Raises:
            NotFoundError: If the page doesn't exist (404)
        """
        endpoint = f"/shops/{self.shop_id}/products.json?page={page}"
        return self.client.get(endpoint)

    def _fetch_page(self, page: int) -> List[Product]:
        """
        Fetch and parse a single page of products.

        Args:
            page: Page number to fetch (1-indexed)

        Returns:
            List of Product objects from the page

        Raises:
            NotFoundError: If the page doesn't exist (404)
        """
        data = self._fetch_page_data(page)
        return [self._parse_product(p) for p in data.get('data', [])]
    
    def _parse_product(self, data: Dict[str, Any]) -> Product:
        """
        Convert API response to Product model.
        
        Uses the parse_product utility function from the models module
        to convert raw API response data into a structured Product object.
        
        Args:
            data: Raw API response dictionary
        
        Returns:
            Product model instance
        """
        return parse_product(data)
