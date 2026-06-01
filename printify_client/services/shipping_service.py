"""
Shipping service for calculating shipping costs.

This module provides the ShippingService class which handles shipping cost
calculations by fetching shipping profiles from the Printify API and applying
first-item and additional-items pricing rules.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from typing import Dict, List, Tuple, Any

from printify_client.client import APIClient
from printify_client.cache import CacheManager
from printify_client.models.order import LineItem, Address
from printify_client.models.product import Product
from printify_client.models.shipping import ShippingCost, ShippingBreakdown
from printify_client.exceptions import ShippingCalculationError


class ShippingService:
    """
    Handles shipping cost calculations.
    
    This service fetches shipping profiles from the Printify API and calculates
    total shipping costs by applying first-item and additional-items pricing
    rules for each line item.
    
    Args:
        client: APIClient instance for making API requests
        cache_manager: CacheManager instance for caching shipping profiles
    
    Example:
        >>> service = ShippingService(client, cache_manager)
        >>> cost = service.calculate_cost(line_items, address, products)
        >>> print(f"Total shipping: {cost}")
    """
    
    def __init__(self, client: APIClient, cache_manager: CacheManager):
        """
        Initialize the shipping service.
        
        Args:
            client: APIClient instance for making API requests
            cache_manager: CacheManager instance for caching shipping profiles
        """
        self.client = client
        self.cache = cache_manager
    
    def calculate_cost(
        self,
        line_items: List[LineItem],
        address: Address,
        products: List[Product]
    ) -> ShippingCost:
        """
        Calculate total shipping cost for line items and destination.
        
        This method:
        1. Groups items by blueprint_id and print_provider_id
        2. Fetches shipping profiles concurrently for each group
        3. Calculates cost for each item using first-item + additional-items pricing
        4. Returns total cost with per-item breakdown
        
        Args:
            line_items: List of items to ship
            address: Destination address
            products: List of products (for looking up blueprint/provider info)
        
        Returns:
            ShippingCost object with total cost and per-item breakdown
        
        Raises:
            ShippingCalculationError: If shipping profile cannot be found
        
        Example:
            >>> items = [LineItem("prod_1", 123, 2)]
            >>> addr = Address("John", "Doe", "john@example.com", "US", ...)
            >>> cost = service.calculate_cost(items, addr, products)
        """
        # Create product lookup map
        product_map = {p.id: p for p in products}
        
        # Group items by blueprint/provider
        groups = self._group_by_blueprint_provider(line_items, product_map)
        
        # Fetch shipping profiles concurrently
        profiles = self._fetch_profiles_concurrently(groups, address)
        
        # Calculate costs for each item
        breakdown = []
        total_cost = Decimal('0')
        
        for item in line_items:
            # Get product info
            product = product_map.get(item.product_id)
            if not product:
                raise ShippingCalculationError(
                    f"Product {item.product_id} not found in provided products list"
                )
            
            # Find matching profile
            profile = self._find_profile(item, product, profiles, address.country)
            
            # Calculate cost for this item
            item_cost = self._calculate_item_cost(item, profile, address.country)
            
            breakdown.append(ShippingBreakdown(
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                cost=item_cost
            ))
            
            total_cost += item_cost
        
        return ShippingCost(
            cost=total_cost,
            currency="USD",
            breakdown=breakdown
        )
    
    def _group_by_blueprint_provider(
        self,
        line_items: List[LineItem],
        product_map: Dict[str, Product]
    ) -> List[Tuple[int, int]]:
        """
        Group items by blueprint_id and print_provider_id.
        
        Returns unique combinations of (blueprint_id, print_provider_id)
        that need shipping profiles fetched.
        
        Args:
            line_items: List of items to group
            product_map: Dictionary mapping product_id to Product objects
        
        Returns:
            List of unique (blueprint_id, print_provider_id) tuples
        
        Raises:
            ShippingCalculationError: If product not found in product_map
        """
        groups = set()
        
        for item in line_items:
            product = product_map.get(item.product_id)
            if not product:
                raise ShippingCalculationError(
                    f"Product {item.product_id} not found in provided products list"
                )
            
            groups.add((product.blueprint_id, product.print_provider_id))
        
        return list(groups)
    
    def _fetch_profiles_concurrently(
        self,
        groups: List[Tuple[int, int]],
        address: Address
    ) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Fetch shipping profiles concurrently using ThreadPoolExecutor.
        
        Uses 5 concurrent workers to fetch shipping profiles for all
        blueprint/provider combinations.
        
        Args:
            groups: List of (blueprint_id, print_provider_id) tuples
            address: Destination address for country-specific profiles
        
        Returns:
            Dictionary mapping (blueprint_id, print_provider_id) to profile data
        """
        profiles = {}
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all fetch tasks
            future_to_group = {
                executor.submit(
                    self._get_shipping_profile,
                    blueprint_id,
                    print_provider_id,
                    address.country
                ): (blueprint_id, print_provider_id)
                for blueprint_id, print_provider_id in groups
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_group):
                group = future_to_group[future]
                try:
                    profile = future.result()
                    profiles[group] = profile
                except Exception as e:
                    # Re-raise with context
                    blueprint_id, print_provider_id = group
                    raise ShippingCalculationError(
                        f"Failed to fetch shipping profile for blueprint {blueprint_id}, "
                        f"provider {print_provider_id}: {str(e)}"
                    )
        
        return profiles
    
    def _get_shipping_profile(
        self,
        blueprint_id: int,
        print_provider_id: int,
        country: str
    ) -> Dict[str, Any]:
        """
        Fetch shipping profile from API with caching.
        
        Caches profiles by blueprint_id, print_provider_id, and country
        to avoid redundant API calls.
        
        Args:
            blueprint_id: Product blueprint identifier
            print_provider_id: Print provider identifier
            country: Destination country code
        
        Returns:
            Shipping profile data from API
        
        Raises:
            ShippingCalculationError: If profile cannot be fetched
        """
        cache_key = f"shipping_profile_{blueprint_id}_{print_provider_id}_{country}"
        
        # Check cache first
        if (cached := self.cache.get(cache_key)) is not None:
            return cached
        
        # Fetch from API
        endpoint = f"/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/shipping.json"
        
        try:
            response = self.client.get(endpoint)
            
            # Cache the result
            self.cache.set(cache_key, response)
            
            return response
        except Exception as e:
            raise ShippingCalculationError(
                f"Failed to fetch shipping profile for blueprint {blueprint_id}, "
                f"provider {print_provider_id}: {str(e)}"
            )
    
    def _find_profile(
        self,
        item: LineItem,
        product: Product,
        profiles: Dict[Tuple[int, int], Dict[str, Any]],
        country: str
    ) -> Dict[str, Any]:
        """
        Find shipping profile for a specific variant and country.
        
        Matches the variant_id and destination country to the appropriate 
        shipping profile within the fetched profiles data.
        
        Args:
            item: Line item with variant_id to match
            product: Product containing blueprint and provider info
            profiles: Dictionary of fetched shipping profiles
            country: Destination country code
        
        Returns:
            Shipping profile data for the variant and country
        
        Raises:
            ShippingCalculationError: If profile cannot be found for variant
        """
        key = (product.blueprint_id, product.print_provider_id)
        profile_data = profiles.get(key)
        
        if not profile_data:
            raise ShippingCalculationError(
                f"No shipping profile found for product {product.id} "
                f"(blueprint {product.blueprint_id}, provider {product.print_provider_id})"
            )
        
        # The API returns profiles in a 'profiles' array
        # Each profile has 'variant_ids' array with variant IDs
        if 'profiles' not in profile_data:
            raise ShippingCalculationError(
                f"Invalid shipping profile response for product {product.id}"
            )
        
        # Find profile that includes this variant and covers the destination country
        matching_profiles = []
        for profile in profile_data['profiles']:
            # Check if variant is in this profile
            if 'variant_ids' in profile and item.variant_id in profile['variant_ids']:
                matching_profiles.append(profile)
        
        if not matching_profiles:
            raise ShippingCalculationError(
                f"No shipping profile found for variant {item.variant_id} "
                f"of product {product.id}"
            )
        
        # Find the profile that covers the destination country
        # Try exact country match first, then REST_OF_THE_WORLD
        for profile in matching_profiles:
            countries = profile.get('countries', [])
            if country in countries:
                return profile
        
        # Fallback to REST_OF_THE_WORLD
        for profile in matching_profiles:
            countries = profile.get('countries', [])
            if 'REST_OF_THE_WORLD' in countries:
                return profile
        
        # If no country match found, raise error
        raise ShippingCalculationError(
            f"No shipping profile found for variant {item.variant_id} "
            f"of product {product.id} shipping to {country}"
        )
    
    def _calculate_item_cost(
        self,
        item: LineItem,
        profile: Dict[str, Any],
        country: str
    ) -> Decimal:
        """
        Calculate shipping cost for an item using first-item + additional-items pricing.
        
        Applies the pricing rule:
        - First item: first_item cost
        - Additional items: additional_items cost each
        
        Args:
            item: Line item with quantity
            profile: Shipping profile with cost data (already matched to country)
            country: Destination country code (for error messages)
        
        Returns:
            Total shipping cost for this item (all quantities)
        
        Raises:
            ShippingCalculationError: If cost data is missing
        """
        # Extract first-item and additional-items costs (in cents)
        first_item_data = profile.get('first_item') or {}
        additional_items_data = profile.get('additional_items') or {}

        first_cost_raw = first_item_data.get('cost')
        if first_cost_raw is None:
            raise ShippingCalculationError(
                "Missing first_item cost data in shipping profile"
            )

        # Default to 0 when additional cost is absent or null
        additional_cost_raw = additional_items_data.get('cost') or 0

        try:
            first_item_cost = Decimal(first_cost_raw) / 100
            additional_item_cost = Decimal(additional_cost_raw) / 100
        except (ArithmeticError, TypeError, ValueError) as e:
            raise ShippingCalculationError(
                f"Invalid shipping cost data in profile: {e}"
            )
        
        # Calculate total cost
        if item.quantity == 1:
            return first_item_cost
        else:
            return first_item_cost + (additional_item_cost * (item.quantity - 1))
