"""
Product-related data models.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Tuple


@dataclass
class Variant:
    """
    Represents a product variant (size/color combination).
    
    Attributes:
        id: Unique variant identifier
        title: Variant name (e.g., "Small / Black")
        is_enabled: Whether variant is available for sale
        price: Variant price in decimal currency (converted from cents)
    """
    id: int
    title: str
    is_enabled: bool
    price: Decimal

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"{self.title} - ${self.price:.2f}"


@dataclass
class Image:
    """
    Represents a product image.
    
    Attributes:
        src: Image URL
        variant_ids: List of variant IDs this image applies to
        position: Image position identifier
        is_default: Whether this is the default product image
    """
    src: str
    variant_ids: List[int]
    position: str
    is_default: bool

    def __str__(self) -> str:
        """String representation for debugging."""
        default_marker = " (default)" if self.is_default else ""
        return f"Image at {self.position}{default_marker}"


@dataclass
class Product:
    """
    Represents a Printify product.
    
    Attributes:
        id: Unique product identifier
        title: Product name
        description: Product description
        blueprint_id: Product type identifier (e.g., 3 for t-shirts)
        print_provider_id: Fulfillment provider identifier
        variants: List of product variants
        images: List of product images
    """
    id: str
    title: str
    description: str
    blueprint_id: int
    print_provider_id: int
    variants: List[Variant]
    images: List[Image]

    @property
    def enabled_variants(self) -> List[Variant]:
        """
        Return only enabled variants.
        
        Returns:
            List of variants where is_enabled is True
        """
        return [v for v in self.variants if v.is_enabled]

    @property
    def default_image(self) -> Optional[Image]:
        """
        Return the default product image.
        
        Returns:
            The image marked as default, or None if no default exists
        """
        return next((img for img in self.images if img.is_default), None)

    @property
    def price_range(self) -> Tuple[Decimal, Decimal]:
        """
        Return (min_price, max_price) for enabled variants.
        
        Returns:
            Tuple of (minimum price, maximum price) for enabled variants.
            Returns (0, 0) if no enabled variants exist.
        """
        enabled = self.enabled_variants
        if not enabled:
            return (Decimal('0'), Decimal('0'))

        prices = [v.price for v in enabled]
        return (min(prices), max(prices))

    def get_variant(self, variant_id: int) -> Optional[Variant]:
        """
        Get variant by ID.
        
        Args:
            variant_id: The variant ID to search for
            
        Returns:
            The matching Variant object, or None if not found
        """
        return next((v for v in self.variants if v.id == variant_id), None)

    def __str__(self) -> str:
        """String representation for debugging."""
        min_price, max_price = self.price_range
        enabled_count = len(self.enabled_variants)

        if min_price == max_price:
            price_str = f"${min_price:.2f}"
        else:
            price_str = f"${min_price:.2f} - ${max_price:.2f}"

        return f"{self.title} ({enabled_count} variants, {price_str})"
