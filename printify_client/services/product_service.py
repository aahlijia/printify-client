"""
Product service for managing Printify products.

This module provides the ProductService class which handles all product-related
operations including fetching, filtering, and caching product data.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
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
        if cached := self.cache.get(cache_key):
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
        if cached := self.cache.get(cache_key):
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
        Fetch multiple pages using ThreadPoolExecutor.
        
        Implements concurrent pagination with 4 workers. Automatically detects
        when no more pages exist by catching 404 errors or empty responses.
        
        Returns:
            List of all Product objects from all pages
        """
        products = []
        page = 1
        max_workers = 4
        
        # Fetch first page to determine if there are more pages
        first_page_products = self._fetch_page(page)
        if not first_page_products:
            return []
        
        products.extend(first_page_products)
        
        # If we got a full page, there might be more pages
        # Printify typically returns 10-20 items per page
        # We'll continue fetching until we get a 404 or empty response
        if len(first_page_products) > 0:
            current_page = 2
            
            # Use ThreadPoolExecutor to fetch multiple pages concurrently
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Keep fetching pages until we hit an empty page or 404
                while True:
                    # Submit a batch of page requests
                    futures = {}
                    for i in range(max_workers):
                        future = executor.submit(self._fetch_page, current_page + i)
                        futures[future] = current_page + i
                    
                    # Collect results from this batch
                    batch_results = {}
                    for future in as_completed(futures):
                        page_num = futures[future]
                        
                        try:
                            page_products = future.result()
                            batch_results[page_num] = page_products or []

                        except NotFoundError:
                            # 404 means we've reached the end of pagination.
                            # Any other error (auth, network, parse) is not an
                            # end-of-pages signal and is allowed to propagate.
                            batch_results[page_num] = []
                    
                    # Add products from successful pages (in order)
                    has_any_products = False
                    for page_num in sorted(batch_results.keys()):
                        if batch_results[page_num]:
                            products.extend(batch_results[page_num])
                            has_any_products = True
                    
                    # If no pages in this batch had products, we're done
                    if not has_any_products:
                        break
                    
                    # Move to the next batch
                    current_page += max_workers
        
        return products
    
    def _fetch_page(self, page: int) -> List[Product]:
        """
        Fetch a single page of products.
        
        Args:
            page: Page number to fetch (1-indexed)
        
        Returns:
            List of Product objects from the page, empty list if page not found
        
        Raises:
            NotFoundError: If the page doesn't exist (404)
        """
        try:
            endpoint = f"/shops/{self.shop_id}/products.json?page={page}"
            data = self.client.get(endpoint) # , params={"page": page}
            
            # Parse products from response
            # The API returns a 'data' key with the list of products
            products_data = data.get('data', [])
            
            return [self._parse_product(p) for p in products_data]
        
        except NotFoundError:
            # 404 means we've reached the end of pagination
            raise
    
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
