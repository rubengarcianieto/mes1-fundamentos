import httpx
import pytest
from pydantic import ValidationError

from day5_weather_client import (
    WeatherResponse,
    fetch_multiple_cities,
    fetch_weather,
    is_retryable,
)

MADRID_LAT, MADRID_LON = 40.4168, -3.7038
LONDON_LAT, LONDON_LON = 51.5074, -0.1278


class UrlRoutingMockHandler:
    """Mock handler that routes responses based on latitude and tracks attempts."""

    def __init__(self, routes: dict[str, list[httpx.Response | Exception]]) -> None:
        self.routes = routes
        self.attempts: dict[str, int] = {lat: 0 for lat in routes}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        lat = request.url.params.get("latitude")
        if lat not in self.routes:
            raise AssertionError(f"Unexpected request for latitude: {lat}")

        current_attempt = self.attempts[lat]
        self.attempts[lat] += 1

        response_sequence = self.routes[lat]
        if current_attempt >= len(response_sequence):
            raise AssertionError(f"Unexpected extra request for latitude: {lat}")

        item = response_sequence[current_attempt]
        if isinstance(item, Exception):
            raise item
        return item


def create_success_response(lat: float, lon: float, temp: float) -> httpx.Response:
    """Helper to generate a standard successful weather HTTP response."""
    return httpx.Response(
        status_code=200,
        json={
            "latitude": lat,
            "longitude": lon,
            "current": {"temperature_2m": temp},
        },
    )


@pytest.mark.asyncio
async def test_fetch_weather_success() -> None:
    """Test successful weather fetch and Pydantic validation."""
    success_resp = create_success_response(MADRID_LAT, MADRID_LON, 22.5)
    handler = UrlRoutingMockHandler({str(MADRID_LAT): [success_resp]})
    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_weather(client, MADRID_LAT, MADRID_LON)

    assert isinstance(result, WeatherResponse)
    assert result.current.temperature_2m == 22.5


@pytest.mark.asyncio
async def test_fetch_weather_exhausts_retries() -> None:
    """Test that exhausting retries raises the HTTPStatusError exception."""
    server_error = httpx.Response(status_code=500)
    handler = UrlRoutingMockHandler({str(MADRID_LAT): [server_error, server_error, server_error]})
    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_weather(
                client,
                MADRID_LAT,
                MADRID_LON,
                max_retries=3,
                initial_delay=0.01,
            )

    assert handler.attempts[str(MADRID_LAT)] == 3


@pytest.mark.asyncio
async def test_fetch_weather_exhausts_retries_timeout() -> None:
    """Test that exhausting retries due to transport timeouts raises a TransportError."""
    timeout_err = httpx.ReadTimeout("Timeout")
    handler = UrlRoutingMockHandler({str(MADRID_LAT): [timeout_err, timeout_err, timeout_err]})
    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(httpx.TransportError):
            await fetch_weather(
                client,
                MADRID_LAT,
                MADRID_LON,
                max_retries=3,
                initial_delay=0.01,
            )

    assert handler.attempts[str(MADRID_LAT)] == 3


@pytest.mark.asyncio
async def test_fetch_weather_no_retry_on_404() -> None:
    """Test that a 404 client error does not retry and fails immediately."""
    not_found = httpx.Response(status_code=404)
    handler = UrlRoutingMockHandler({str(MADRID_LAT): [not_found]})
    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_weather(
                client,
                MADRID_LAT,
                MADRID_LON,
                max_retries=3,
                initial_delay=0.01,
            )

    assert handler.attempts[str(MADRID_LAT)] == 1


@pytest.mark.asyncio
async def test_fetch_weather_recovers_from_timeout() -> None:
    """Test that a transient transport error or timeout is successfully retried."""
    success_resp = create_success_response(MADRID_LAT, MADRID_LON, 15.0)
    timeout_err = httpx.ReadTimeout("Timeout")
    handler = UrlRoutingMockHandler({str(MADRID_LAT): [timeout_err, success_resp]})
    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_weather(
            client,
            MADRID_LAT,
            MADRID_LON,
            max_retries=3,
            initial_delay=0.01,
        )

    assert result.current.temperature_2m == 15.0
    assert handler.attempts[str(MADRID_LAT)] == 2


@pytest.mark.asyncio
async def test_fetch_weather_invalid_data_raises_validation_error() -> None:
    """Test that malformed JSON payloads trigger a Pydantic ValidationError."""
    bad_resp = httpx.Response(
        status_code=200,
        json={"latitude": "invalid_string", "longitude": MADRID_LON, "current": {}},
    )
    transport = httpx.MockTransport(UrlRoutingMockHandler({str(MADRID_LAT): [bad_resp]}))

    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ValidationError):
            await fetch_weather(client, MADRID_LAT, MADRID_LON)


@pytest.mark.asyncio
async def test_fetch_weather_invalid_json_raises_value_error() -> None:
    """Test that a non-JSON response body raises a ValueError."""
    bad_resp = httpx.Response(status_code=200, content=b"Not a JSON body")
    transport = httpx.MockTransport(UrlRoutingMockHandler({str(MADRID_LAT): [bad_resp]}))

    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ValueError, match="Invalid JSON response"):
            await fetch_weather(client, MADRID_LAT, MADRID_LON)


@pytest.mark.asyncio
async def test_fetch_weather_invalid_max_retries_raises_value_error() -> None:
    """Test that max_retries <= 0 raises a ValueError."""
    transport = httpx.MockTransport(UrlRoutingMockHandler({}))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ValueError, match="max_retries must be greater than 0"):
            await fetch_weather(client, MADRID_LAT, MADRID_LON, max_retries=0)


@pytest.mark.asyncio
async def test_fetch_multiple_cities_mixed_results() -> None:
    """Test fetching multiple cities with mixed success and failure."""
    cities = {
        "Madrid": (MADRID_LAT, MADRID_LON),
        "London": (LONDON_LAT, LONDON_LON),
    }
    madrid_resp = create_success_response(MADRID_LAT, MADRID_LON, 25.0)
    server_error = httpx.Response(status_code=500)

    routes = {
        str(MADRID_LAT): [madrid_resp],
        str(LONDON_LAT): [server_error, server_error, server_error],
    }
    handler = UrlRoutingMockHandler(routes)
    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        results = await fetch_multiple_cities(
            client,
            cities,
            max_retries=3,
            initial_delay=0.01,
        )

    assert isinstance(results["Madrid"], WeatherResponse)
    assert results["Madrid"].current.temperature_2m == 25.0
    assert isinstance(results["London"], httpx.HTTPStatusError)
    assert handler.attempts[str(MADRID_LAT)] == 1
    assert handler.attempts[str(LONDON_LAT)] == 3


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (httpx.HTTPStatusError("Err", request=httpx.Request("GET", "http://test"), response=httpx.Response(500)), True),
        (httpx.HTTPStatusError("Err", request=httpx.Request("GET", "http://test"), response=httpx.Response(404)), False),
        (httpx.ReadTimeout("Timeout"), True),
        (ValueError("Invalid"), False),
    ],
)
def test_is_retryable(error: Exception, expected: bool) -> None:
    """Test pure is_retryable classification logic for various exception types."""
    assert is_retryable(error) is expected