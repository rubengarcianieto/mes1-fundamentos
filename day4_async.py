import asyncio
import time
import httpx
import requests


# Fetch a single post asynchronously
async def fetch_post(client: httpx.AsyncClient, post_id: int) -> dict:
    response = await client.get(
        f"https://jsonplaceholder.typicode.com/posts/{post_id}"
    )
    response.raise_for_status()
    return response.json()


# Fetch multiple posts concurrently using asyncio.gather
async def fetch_many_async(ids: list[int]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        tasks = [fetch_post(client, i) for i in ids]
        return await asyncio.gather(*tasks)


# Fetch multiple posts sequentially using traditional requests
def fetch_many_sync(ids: list[int]) -> list[dict]:
    results = []
    for i in ids:
        response = requests.get(
            f"https://jsonplaceholder.typicode.com/posts/{i}"
        )
        response.raise_for_status()
        results.append(response.json())
    return results


# Fault-tolerant main function that handles missing resources or network errors
async def main_tolerant():
    # ID 9999 is included to intentionally trigger an HTTP 404 error
    ids_with_error = [1, 2, 9999, 4]

    async with httpx.AsyncClient() as client:
        tasks = [fetch_post(client, i) for i in ids_with_error]

        # return_exceptions=True prevents the entire batch from crashing on error
        results = await asyncio.gather(*tasks, return_exceptions=True)

        print("\n--- Fault Tolerant Execution Results ---")
        for result in results:
            if isinstance(result, Exception):
                print("Failed:", result)
            else:
                print("Success - Post ID:", result["id"])


# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    ids = list(range(1, 11))  # 10 posts for benchmarking

    # 1. Asynchronous Benchmark
    start_time = time.perf_counter()
    asyncio.run(fetch_many_async(ids))
    async_duration = time.perf_counter() - start_time
    print(f"Async (concurrent): {async_duration:.2f}s")

    # 2. Synchronous Benchmark
    start_time = time.perf_counter()
    fetch_many_sync(ids)
    sync_duration = time.perf_counter() - start_time
    print(f"Sync (sequential):   {sync_duration:.2f}s")

    # 3. Fault-Tolerant Execution
    asyncio.run(main_tolerant())