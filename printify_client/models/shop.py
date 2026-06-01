"""
Shop-related data models.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ShopInfo:
    """
    Represents Printify shop information.
    
    Attributes:
        id: Printify shop identifier
        title: Shop name/title
        sales_channel: Sales channel type (optional)
    """
    id: str
    title: str
    sales_channel: Optional[str] = None

    def __str__(self) -> str:
        """String representation for debugging."""
        channel_info = f" ({self.sales_channel})" if self.sales_channel else ""
        return f"Shop {self.id}: {self.title}{channel_info}"
