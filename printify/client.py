"""
API client for interacting with the Printify REST API.

This module provides the APIClient class which handles all HTTP communication
with the Printify API, including authentication, retry logic, and error handling.
"""

import time
from typing import Dict, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    AuthenticationError,
    NotFoundError,
    APIError,
    TimeoutError as PrintifyTimeoutError,
)


class APIClient:
    """
    HTTP client for Printify API with retry logic and connection pooling.
    
    This client handles:
    - Bearer token authentication
    - Automatic retries with exponential backoff
    - Connection pooling for improved performance
    - Comprehensive error handling
    - SSL verification
    
    Args:
        api_key: Printify API key for authentication
        timeout: Request timeout in seconds (default: 20)
        max_retries: Maximum number of retry attempts (default: 3)
        pool_connections: Number of connection pools to cache (default: 10)
        pool_maxsize: Maximum number of connections in each pool (default: 20)
    
    Example:
        >>> client = APIClient(api_key="your_api_key")
        >>> data = client.get("/shops/12345/products.json")
    """
    
    BASE_URL = "https://api.printify.com/v1"
    
    def __init__(
        self,
        api_key: str,
        timeout: int = 20,
        max_retries: int = 3,
        pool_connections: int = 10,
        pool_maxsize: int = 20,
    ):
        """
        Initialize the API client with authentication and connection pooling.
        
        Args:
            api_key: Printify API key for Bearer token authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            pool_connections: Number of connection pools to cache
            pool_maxsize: Maximum number of connections to save in the pool
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Set up session with connection pooling
        self.session = requests.Session()
        
        # Configure HTTPAdapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Configure Bearer token authentication
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make GET request to the Printify API.
        
        Args:
            endpoint: API endpoint path (e.g., "/shops/123/products.json")
            params: Optional query parameters
        
        Returns:
            Parsed JSON response as dictionary
        
        Raises:
            AuthenticationError: If API key is invalid (401)
            NotFoundError: If resource is not found (404)
            APIError: For other HTTP errors
            PrintifyTimeoutError: If request times out
        
        Example:
            >>> client.get("/shops/123/products.json", params={"page": 1})
        """
        return self._make_request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make POST request to the Printify API.
        
        Args:
            endpoint: API endpoint path (e.g., "/shops/123/orders.json")
            data: Request body data to be sent as JSON
        
        Returns:
            Parsed JSON response as dictionary
        
        Raises:
            AuthenticationError: If API key is invalid (401)
            NotFoundError: If resource is not found (404)
            APIError: For other HTTP errors
            PrintifyTimeoutError: If request times out
        
        Example:
            >>> client.post("/shops/123/orders.json", data={"line_items": [...]})
        """
        return self._make_request("POST", endpoint, data=data)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Internal method to make HTTP requests with retry logic.
        
        Implements exponential backoff retry strategy for transient errors.
        Handles authentication, not found, and other API errors appropriately.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Optional query parameters
            data: Optional request body data
        
        Returns:
            Parsed JSON response as dictionary
        
        Raises:
            AuthenticationError: If API key is invalid (401)
            NotFoundError: If resource is not found (404)
            APIError: For other HTTP errors
            PrintifyTimeoutError: If request times out after all retries
        """
        url = f"{self.BASE_URL}{endpoint}"
        backoff_delays = [0.3, 0.6, 1.2]
        
        for attempt in range(self.max_retries + 1):
            try:
                # Make the HTTP request
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    timeout=self.timeout,
                )
                
                # Handle authentication errors immediately (don't retry)
                if response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid API key. Please check your Printify API key."
                    )
                
                # Handle not found errors immediately (don't retry)
                if response.status_code == 404:
                    raise NotFoundError("Resource", endpoint)
                
                # Check if we should retry this status code
                if self._should_retry(response.status_code) and attempt < self.max_retries:
                    time.sleep(backoff_delays[attempt])
                    continue
                
                # Raise for other HTTP errors
                if not response.ok:
                    error_message = "Request failed"
                    error_response = None
                    
                    try:
                        error_response = response.json()
                        error_message = error_response.get("message", error_message)
                    except Exception:
                        error_message = response.text or error_message
                    
                    raise APIError(
                        status_code=response.status_code,
                        message=error_message,
                        response=error_response,
                    )
                
                # Success - return parsed JSON
                return response.json()
            
            except requests.exceptions.Timeout:
                # Retry on timeout if we have attempts left
                if attempt < self.max_retries:
                    time.sleep(backoff_delays[attempt])
                    continue
                
                # Out of retries - raise timeout error
                raise PrintifyTimeoutError(
                    f"Request timed out after {self.timeout} seconds"
                )
            
            except requests.exceptions.RequestException as e:
                # Handle other request exceptions
                # Don't retry these - they're usually not transient
                if not isinstance(e, requests.exceptions.Timeout):
                    raise APIError(
                        status_code=0,
                        message=f"Request failed: {str(e)}",
                    )
        
        # Should never reach here, but just in case
        raise APIError(
            status_code=0,
            message="Request failed after all retry attempts",
        )
    
    def _should_retry(self, status_code: int) -> bool:
        """
        Determine if a request should be retried based on status code.
        
        Retryable status codes are:
        - 429: Too Many Requests (rate limiting)
        - 500: Internal Server Error
        - 502: Bad Gateway
        - 503: Service Unavailable
        - 504: Gateway Timeout
        
        Args:
            status_code: HTTP status code from the response
        
        Returns:
            True if the request should be retried, False otherwise
        """
        return status_code in [429, 500, 502, 503, 504]
