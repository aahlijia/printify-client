"""
Exception classes for the Printify Python library.

This module defines custom exceptions for handling various error scenarios
when interacting with the Printify API.
"""

from typing import Optional, Dict, Any


class PrintifyError(Exception):
    """
    Base exception for all Printify library errors.
    
    All custom exceptions in this library inherit from this base class,
    making it easy to catch any Printify-related error.
    """
    pass


class AuthenticationError(PrintifyError):
    """
    Raised when API key is invalid or missing.
    
    This exception is raised when:
    - The API key is not provided and not found in environment variables
    - The API key is invalid (401 response from API)
    - Authentication fails for any other reason
    
    Example:
        >>> raise AuthenticationError("Invalid API key provided")
    """
    
    def __init__(self, message: str = "Authentication failed. Please check your API key."):
        super().__init__(message)
        self.message = message


class NotFoundError(PrintifyError):
    """
    Raised when a resource is not found (404).
    
    This exception includes information about what type of resource
    was not found and its identifier for better debugging.
    
    Args:
        resource_type: The type of resource that was not found (e.g., "Product", "Shop", "Order")
        identifier: The identifier used to look up the resource (e.g., product ID, shop name)
    
    Attributes:
        resource_type: The type of resource that was not found
        identifier: The identifier that was used in the lookup
    
    Example:
        >>> raise NotFoundError("Product", "prod_123")
        NotFoundError: Product not found: prod_123
    """
    
    def __init__(self, resource_type: str, identifier: str):
        message = f"{resource_type} not found: {identifier}"
        super().__init__(message)
        self.resource_type = resource_type
        self.identifier = identifier


class APIError(PrintifyError):
    """
    Raised when API returns an error response.
    
    This exception wraps HTTP errors from the Printify API and includes
    the status code, error message, and optionally the full response
    for debugging purposes.
    
    Args:
        status_code: HTTP status code from the API response
        message: Error message describing what went wrong
        response: Optional full response data from the API for debugging
    
    Attributes:
        status_code: The HTTP status code
        message: The error message
        response: The full API response (if available)
    
    Example:
        >>> raise APIError(500, "Internal server error", {"error": "Database connection failed"})
        APIError: API Error 500: Internal server error
    """
    
    def __init__(self, status_code: int, message: str, response: Optional[Dict[str, Any]] = None):
        error_message = f"API Error {status_code}: {message}"
        super().__init__(error_message)
        self.status_code = status_code
        self.message = message
        self.response = response


class ValidationError(PrintifyError):
    """
    Raised when input validation fails.
    
    This exception is raised before making API calls when the provided
    input data does not meet the required format or constraints.
    
    Example:
        >>> raise ValidationError("shop_id or shop_name must be provided")
    """
    pass


class ShippingCalculationError(PrintifyError):
    """
    Raised when shipping cost calculation fails.
    
    This exception is raised when:
    - Shipping profile cannot be found for a product/destination combination
    - Required shipping data is missing
    - Calculation logic encounters an error
    
    Example:
        >>> raise ShippingCalculationError("No shipping profile found for variant 123 to country US")
    """
    pass


class TimeoutError(PrintifyError):
    """
    Raised when API request times out.
    
    This exception is raised when a request to the Printify API
    exceeds the configured timeout threshold.
    
    Example:
        >>> raise TimeoutError("Request timed out after 20 seconds")
    """
    pass
