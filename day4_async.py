import asyncio
import time

import httpx
import requests


async def fetch_post(client: httpx.AsyncClient, post_id: int) -> dict:
    # await hands control to the event loop while the network replies
    response = await client.get(f"https://jsonplaceholder.typicode.com/posts/{post_id}")
    response.raise_for_status()
    return response.json()


async def fetch_many_async(ids: list[int]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        tasks = [fetch_post(client, i) for i in ids]
        return await asyncio.gather(*tasks)


def fetch_many_sync(ids: list[int]) -> list[dict]:
    results = []
    for i in ids:
        r = requests.get(f"https://jsonplaceholder.typicode.com/posts/{i}")
        r.raise_for_status()
        results.append(r.json())
    return results


# Part 1: concurrent vs sequential timing
ids = list(range(1, 11))

start = time.perf_counter()
asyncio.run(fetch_many_async(ids))
print(f"Async (concurrent): {time.perf_counter() - start:.2f}s")

start = time.perf_counter()
fetch_many_sync(ids)
print(f"Sync (sequential): {time.perf_counter() - start:.2f}s")


# Part 2: what happens when one call fails
ids_with_error = [1, 2, 99999, 4]  # 99999 does not exist (404)


async def main_strict():
    async with httpx.AsyncClient() as client:
        tasks = [fetch_post(client, i) for i in ids_with_error]
        return await asyncio.gather(*tasks)  # the first error aborts everything


async def main_tolerant():
    async with httpx.AsyncClient() as client:
        tasks = [fetch_post(client, i) for i in ids_with_error]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                print("Failed:", result)
            else:
                print("OK:", result["id"])


try:
    asyncio.run(main_strict())
except httpx.HTTPStatusError as error:
    print("Strict mode failed, all results lost:", error)

asyncio.run(main_tolerant())