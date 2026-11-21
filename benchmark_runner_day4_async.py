"""Benchmark runner for day4_async.py comparing async vs sync execution."""

import asyncio
import csv
import statistics
import time

from day4_async import fetch_many_async, fetch_many_sync

ITERATIONS = 20
POST_IDS = list(range(1, 11))
OUTPUT_FILE = "benchmark_results.csv"


def run_benchmark(iterations: int, ids: list[int]) -> list[dict[str, float | int]]:
    """Run async and sync fetch functions multiple times and record durations."""
    results: list[dict[str, float | int]] = []

    for i in range(1, iterations + 1):
        # Measure async execution
        start_async = time.perf_counter()
        asyncio.run(fetch_many_async(ids))
        async_duration = time.perf_counter() - start_async

        # Measure sync execution
        start_sync = time.perf_counter()
        fetch_many_sync(ids)
        sync_duration = time.perf_counter() - start_sync

        results.append(
            {
                "iteration": i,
                "async_seconds": round(async_duration, 4),
                "sync_seconds": round(sync_duration, 4),
            }
        )
        print(
            f"Run {i:02d}/{iterations} -> "
            f"Async: {async_duration:.4f}s | Sync: {sync_duration:.4f}s"
        )

    return results


def save_to_csv(data: list[dict[str, float | int]], filepath: str) -> None:
    """Save benchmark results to a CSV file."""
    fieldnames = ["iteration", "async_seconds", "sync_seconds"]
    with open(filepath, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    print(f"Starting benchmark ({ITERATIONS} iterations)...\n")
    benchmark_data = run_benchmark(ITERATIONS, POST_IDS)
    save_to_csv(benchmark_data, OUTPUT_FILE)

    # Calculate quick summary stats using standard library
    async_times = [row["async_seconds"] for row in benchmark_data]
    sync_times = [row["sync_seconds"] for row in benchmark_data]

    print(f"\nResults saved to {OUTPUT_FILE}")
    print(f"Async Mean: {statistics.mean(async_times):.4f}s")
    print(f"Sync Mean:  {statistics.mean(sync_times):.4f}s")
