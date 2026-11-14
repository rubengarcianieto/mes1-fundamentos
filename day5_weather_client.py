import asyncio
import json

import httpx
from pydantic import BaseModel, ValidationError

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_TIMEOUT = 10.0


class CurrentWeather(BaseModel):
    """Sub-model representing current weather measurements."""

    temperature_2m: float


class WeatherResponse(BaseModel):
    """Main model representing the Open-Meteo API response."""

    latitude: float
    longitude: float
    current: CurrentWeather


def is_retryable(error: Exception) -> bool:
    """Determine if an error is transient and safe to retry."""
    if isinstance(error, httpx.TransportError):
        return True
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code >= 500
    return False


async def fetch_weather(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    max_retries: int = 3,
    initial_delay: float = 0.5,
) -> WeatherResponse:
    """Fetch weather for given coordinates with retry logic and validation.

    Raises:
        ValueError: If max_retries is <= 0 or response JSON is invalid.
        httpx.HTTPStatusError: If a client error (4xx) or exhausted 5xx occurs.
        httpx.TransportError: If network connection or timeout fails repeatedly.
        ValidationError: If response JSON does not match the Pydantic schema.
    """
    if max_retries <= 0:
        raise ValueError("max_retries must be greater than 0")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m",
    }

    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            response = await client.get(WEATHER_API_URL, params=params)
            response.raise_for_status()

            try:
                data = response.json()
            except json.JSONDecodeError as error:
                raise ValueError("Invalid JSON response from server") from error

            return WeatherResponse.model_validate(data)

        except (httpx.TransportError, httpx.HTTPStatusError) as error:
            if not is_retryable(error) or attempt == max_retries:
                raise

            await asyncio.sleep(delay)
            delay *= 2.0

    raise RuntimeError("Unexpected end of retry loop")


async def fetch_multiple_cities(
    client: httpx.AsyncClient,
    cities: dict[str, tuple[float, float]],
    *,
    max_retries: int = 3,
    initial_delay: float = 0.5,
) -> dict[str, WeatherResponse | BaseException]:
    """Fetch weather concurrently for multiple cities using asyncio.gather."""
    names = list(cities.keys())
    coords = list(cities.values())
    tasks = [
        fetch_weather(
            client,
            lat,
            lon,
            max_retries=max_retries,
            initial_delay=initial_delay,
        )
        for lat, lon in coords
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return dict(zip(names, results, strict=True))


if __name__ == "__main__":
    target_cities = {
        "Madrid": (40.4168, -3.7038),
        "London": (51.5074, -0.1278),
        "Paris": (48.8566, 2.3522),
    }

    async def main() -> None:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            results = await fetch_multiple_cities(client, target_cities)
            for city_name, result in results.items():
                if isinstance(result, BaseException):
                    print(f"Failed to fetch {city_name}: {result!r}")
                else:
                    temp = result.current.temperature_2m
                    print(f"OK: {city_name} temperature is {temp}°C")

    asyncio.run(main())