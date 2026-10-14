import asyncio
import json
import time

import httpx
import requests

POSTS_URL = "https://jsonplaceholder.typicode.com/posts"
REQUEST_TIMEOUT = 10.0  # seconds, applied to each phase (connect, read, ...)


async def fetch_post(client: httpx.AsyncClient, post_id: int) -> dict:
    """Fetch one post; raise HTTPStatusError or ValueError on failure."""
    response = await client.get(f"{POSTS_URL}/{post_id}")
    response.raise_for_status()  # raises on 4xx/5xx
    try:
        return response.json()
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON for post {post_id}") from error


async def fetch_many_async(ids: list[int]) -> list[dict]:
    """Fetch posts concurrently; the first failure aborts the batch."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        tasks = [fetch_post(client, post_id) for post_id in ids]
        return await asyncio.gather(*tasks)


def fetch_many_sync(ids: list[int]) -> list[dict]:
    """Fetch posts one after another (baseline for the benchmark)."""
    results = []
    for post_id in ids:
        response = requests.get(f"{POSTS_URL}/{post_id}", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        results.append(response.json())
    return results


async def fetch_many_tolerant(ids: list[int]) -> list[dict | Exception]:
    """Fetch posts concurrently; failures are returned in place, not raised."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        tasks = [fetch_post(client, post_id) for post_id in ids]
        return await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    ids = list(range(1, 11))

    start_time = time.perf_counter()
    asyncio.run(fetch_many_async(ids))
    print(f"Async (concurrent): {time.perf_counter() - start_time:.2f}s")

    start_time = time.perf_counter()
    fetch_many_sync(ids)
    print(f"Sync (sequential): {time.perf_counter() - start_time:.2f}s")

    ids_with_error = [1, 2, 9999, 4]  # 9999 does not exist, so it returns 404
    for result in asyncio.run(fetch_many_tolerant(ids_with_error)):
        if isinstance(result, Exception):
            print("Failed:", repr(result))
        else:
            print("OK:", result["id"])
