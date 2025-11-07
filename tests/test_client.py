"""Tests for API client."""

import time
import responses
from printify_client.client import APIClient
from printify_client.exceptions import (
    AuthenticationError,
    NotFoundError,
    APIError,
    TimeoutError as PrintifyTimeoutError,
)


@responses.activate
def test_client_successful_get_request():
    """Test successful GET request."""
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/123/products.json",
        json={"data": [{"id": "prod_1"}]},
        status=200,
    )
    
    client = APIClient(api_key="test_key")
    result = client.get("/shops/123/products.json")
    
    assert result == {"data": [{"id": "prod_1"}]}
    assert len(responses.calls) == 1
    assert responses.calls[0].request.headers["Authorization"] == "Bearer test_key"


@responses.activate
def test_client_successful_post_request():
    """Test successful POST request."""
    responses.add(
        responses.POST,
        "https://api.printify.com/v1/shops/123/orders.json",
        json={"id": "order_1", "status": "pending"},
        status=201,
    )
    
    client = APIClient(api_key="test_key")
    result = client.post("/shops/123/orders.json", data={"line_items": []})
    
    assert result == {"id": "order_1", "status": "pending"}
    assert len(responses.calls) == 1


@responses.activate
def test_client_bearer_token_authentication():
    """Test that Bearer token is included in request headers."""
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        json={"success": True},
        status=200,
    )
    
    client = APIClient(api_key="my_secret_key")
    client.get("/test")
    
    assert responses.calls[0].request.headers["Authorization"] == "Bearer my_secret_key"
    assert responses.calls[0].request.headers["Content-Type"] == "application/json"


@responses.activate
def test_client_authentication_error():
    """Test authentication error (401) raises AuthenticationError."""
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/123/products.json",
        json={"error": "Unauthorized"},
        status=401,
    )
    
    client = APIClient(api_key="invalid_key")
    
    try:
        client.get("/shops/123/products.json")
        assert False, "Should have raised AuthenticationError"
    except AuthenticationError as e:
        assert "Invalid API key" in str(e)


@responses.activate
def test_client_not_found_error():
    """Test not found error (404) raises NotFoundError."""
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/shops/123/products/999.json",
        json={"error": "Not found"},
        status=404,
    )
    
    client = APIClient(api_key="test_key")
    
    try:
        client.get("/shops/123/products/999.json")
        assert False, "Should have raised NotFoundError"
    except NotFoundError as e:
        assert e.resource_type == "Resource"
        assert "/shops/123/products/999.json" in e.identifier


@responses.activate
def test_client_retry_on_429():
    """Test retry logic with 429 (rate limit) status code."""
    # First two attempts return 429, third succeeds
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        json={"error": "Rate limited"},
        status=429,
    )
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        json={"error": "Rate limited"},
        status=429,
    )
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        json={"success": True},
        status=200,
    )
    
    client = APIClient(api_key="test_key", max_retries=3)
    result = client.get("/test")
    
    assert result == {"success": True}
    assert len(responses.calls) == 3


@responses.activate
def test_client_retry_on_500():
    """Test retry logic with 500 (server error) status code."""
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        json={"error": "Internal server error"},
        status=500,
    )
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        json={"success": True},
        status=200,
    )
    
    client = APIClient(api_key="test_key", max_retries=3)
    result = client.get("/test")
    
    assert result == {"success": True}
    assert len(responses.calls) == 2


@responses.activate
def test_client_retry_on_502():
    """Test retry logic with 502 (bad gateway) status code."""
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        status=502,
    )
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        json={"success": True},
        status=200,
    )
    
    client = APIClient(api_key="test_key", max_retries=3)
    result = client.get("/test")
    
    assert result == {"success": True}
    assert len(responses.calls) == 2


@responses.activate
def test_client_retry_on_503():
    """Test retry logic with 503 (service unavailable) status code."""
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        status=503,
    )
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        json={"success": True},
        status=200,
    )
    
    client = APIClient(api_key="test_key", max_retries=3)
    result = client.get("/test")
    
    assert result == {"success": True}
    assert len(responses.calls) == 2


@responses.activate
def test_client_retry_on_504():
    """Test retry logic with 504 (gateway timeout) status code."""
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        status=504,
    )
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        json={"success": True},
        status=200,
    )
    
    client = APIClient(api_key="test_key", max_retries=3)
    result = client.get("/test")
    
    assert result == {"success": True}
    assert len(responses.calls) == 2


@responses.activate
def test_client_exponential_backoff():
    """Test exponential backoff delays between retries."""
    for _ in range(3):
        responses.add(
            responses.GET,
            "https://api.printify.com/v1/test",
            status=500,
        )
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        json={"success": True},
        status=200,
    )
    
    client = APIClient(api_key="test_key", max_retries=3)
    
    start_time = time.time()
    result = client.get("/test")
    elapsed = time.time() - start_time
    
    # Should have delays of 0.3, 0.6, 1.2 seconds = 2.1 seconds total
    assert elapsed >= 2.0
    assert result == {"success": True}
    assert len(responses.calls) == 4


@responses.activate
def test_client_max_retries_exceeded():
    """Test that APIError is raised after max retries exceeded."""
    for _ in range(5):
        responses.add(
            responses.GET,
            "https://api.printify.com/v1/test",
            json={"error": "Server error"},
            status=500,
        )
    
    client = APIClient(api_key="test_key", max_retries=3)
    
    try:
        client.get("/test")
        assert False, "Should have raised APIError"
    except APIError as e:
        assert e.status_code == 500
        assert "Request failed" in str(e) or "Server error" in str(e)
    
    # Should have made 4 attempts (initial + 3 retries)
    assert len(responses.calls) == 4


@responses.activate
def test_client_api_error_with_response():
    """Test APIError includes response data."""
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        json={"error": "Bad request", "details": "Invalid parameter"},
        status=400,
    )
    
    client = APIClient(api_key="test_key")
    
    try:
        client.get("/test")
        assert False, "Should have raised APIError"
    except APIError as e:
        assert e.status_code == 400
        assert e.response is not None
        assert e.response.get("error") == "Bad request"


@responses.activate
def test_client_no_retry_on_400():
    """Test that 400 errors are not retried."""
    responses.add(
        responses.GET,
        "https://api.printify.com/v1/test",
        json={"error": "Bad request"},
        status=400,
    )
    
    client = APIClient(api_key="test_key", max_retries=3)
    
    try:
        client.get("/test")
        assert False, "Should have raised APIError"
    except APIError:
        pass
    
    # Should only make 1 attempt (no retries for 400)
    assert len(responses.calls) == 1
