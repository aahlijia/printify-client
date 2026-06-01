"""
Order service for creating and managing Printify orders.

This module provides the OrderService class which handles order creation
and validation logic for the Printify API.
"""

from typing import List, Optional

from printify_client.client import APIClient
from printify_client.models import parse_order
from printify_client.models.order import Order, LineItem, Address
from printify_client.exceptions import ValidationError, APIError


class OrderService:
    """
    Handles order-related operations for a Printify shop.
    
    This service manages order creation, including input validation,
    API request formatting, and response parsing.
    
    Args:
        client: APIClient instance for making API requests
        shop_id: Printify shop identifier
    
    Example:
        >>> client = APIClient(api_key="your_api_key")
        >>> service = OrderService(client, shop_id="12345")
        >>> order = service.create_order(line_items, address)
    """
    
    def __init__(self, client: APIClient, shop_id: str):
        """
        Initialize the OrderService.
        
        Args:
            client: APIClient instance for making API requests
            shop_id: Printify shop identifier
        """
        self.client = client
        self.shop_id = shop_id
    
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
        
        This method validates the input, builds the API request payload,
        makes the POST request to create the order, and parses the response
        into an Order object.
        
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
            >>> order = service.create_order(items, address, external_id="order_12345")
        """
        # Validate required fields
        self._validate_order_input(line_items, shipping_address)
        
        # Build API request payload
        payload = self._build_order_payload(
            line_items=line_items,
            shipping_address=shipping_address,
            external_id=external_id,
            label=label,
            send_notification=send_notification,
        )
        
        # Make POST request to create order
        endpoint = f"/shops/{self.shop_id}/orders.json"
        
        try:
            response_data = self.client.post(endpoint, data=payload)
        except APIError as e:
            # Re-raise with additional context
            raise APIError(
                status_code=e.status_code,
                message=f"Failed to create order: {e.message}",
                response=e.response,
            )
        
        # Parse API response to Order model
        order = self._parse_order_response(response_data)
        
        return order
    
    def _validate_order_input(
        self,
        line_items: List[LineItem],
        shipping_address: Address,
    ) -> None:
        """
        Validate order input before making API call.
        
        Args:
            line_items: List of items to validate
            shipping_address: Address to validate
        
        Raises:
            ValidationError: If validation fails
        """
        # Validate line items
        if not line_items:
            raise ValidationError("At least one line item is required to create an order")
        
        for item in line_items:
            if not item.product_id:
                raise ValidationError("Line item product_id is required")
            if not item.variant_id:
                raise ValidationError("Line item variant_id is required")
            if item.quantity <= 0:
                raise ValidationError("Line item quantity must be greater than 0")
        
        # Validate shipping address required fields
        required_address_fields = [
            ('first_name', shipping_address.first_name),
            ('last_name', shipping_address.last_name),
            ('email', shipping_address.email),
            ('country', shipping_address.country),
            ('region', shipping_address.region),
            ('city', shipping_address.city),
            ('zip_code', shipping_address.zip_code),
            ('address1', shipping_address.address1),
        ]
        
        for field_name, field_value in required_address_fields:
            if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                raise ValidationError(f"Shipping address {field_name} is required")
    
    def _build_order_payload(
        self,
        line_items: List[LineItem],
        shipping_address: Address,
        external_id: Optional[str],
        label: Optional[str],
        send_notification: bool,
    ) -> dict:
        """
        Build API request payload for order creation.
        
        Args:
            line_items: List of items to include
            shipping_address: Destination address
            external_id: Optional external order reference
            label: Optional customer label
            send_notification: Whether to send notification
        
        Returns:
            Dictionary formatted for Printify API request
        """
        payload = {
            'line_items': [item.to_dict() for item in line_items],
            'address_to': shipping_address.to_dict(),
            'send_notification': send_notification,
        }
        
        if external_id:
            payload['external_id'] = external_id
        
        if label:
            payload['label'] = label
        
        return payload
    
    def _parse_order_response(self, data: dict) -> Order:
        """
        Parse API response to Order model.

        Delegates to the shared ``parse_order`` helper so order parsing has a
        single implementation across the library.

        Args:
            data: API response data

        Returns:
            Order object
        """
        return parse_order(data)
