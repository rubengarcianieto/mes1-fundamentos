# Benchmark: async vs sync HTTP requests

> Measured on <YYYY-MM-DD>. This is a small learning experiment, not a
> general measurement.

## Question

Is fetching 10 posts concurrently (`httpx` + `asyncio.gather`) faster than
fetching them one by one (`requests`)? By how much?

## Method

- **Runner:** [`benchmark_runner_day4_async.py`](../benchmark_runner_day4_async.py)
  imports `fetch_many_async` and `fetch_many_sync` from `day4_async.py`.
- **Workload:** 10 GET requests to `https://jsonplaceholder.typicode.com/posts/{id}`,
  with ids 1 to 10.
- **Async version:** one `httpx.AsyncClient`, with all 10 requests launched
  together by `asyncio.gather`.
- **Sync version:** 10 sequential `requests.get` calls. There is no
  `requests.Session`, so each call sets up its own connection.
- **Repetitions:** 20 iterations. In each one, the async version runs first and
  then the sync version.
- **Timing:** `time.perf_counter()` around each whole call, rounded to 4
  decimals.
- **Raw data:** [`benchmark_results.csv`](../benchmark_results.csv).
- **Environment:** Ubuntu, Python 3.14, httpx 0.28.1, requests 2.34.2,
  <Wi-Fi or cable>.

To repeat it: `uv run python benchmark_runner_day4_async.py`.

## Results

Time in seconds to fetch the 10 posts (20 runs each):

| | Async | Sync |
|---|---|---|
| Minimum | 1.90 | 13.73 |
| Median | 2.12 | 14.44 |
| Mean | 2.18 | 14.73 |
| Maximum | 2.69 | 16.39 |
| Standard deviation | 0.22 | 0.79 |

- On average, the sync version took **6.8 times** as long as the async one.
  Run by run, the ratio ranged from 5.3 to 8.3 (median 6.7).
- The slowest async run (2.69 s) was far faster than the fastest sync run
  (13.73 s).
- The sync version needed about 1.5 s per request on average (14.73 s for 10),
  so each request spends most of its time waiting for the network.
- The first three async runs were a bit slower (2.66, 2.26 and 2.69 s) than the
  rest (mean 2.11 s for runs 4 to 20). This may be a warm-up effect, but it was
  not investigated.
- Relative to its mean, the async version varied more (about 10%) than the sync
  version (about 5%).

## Conclusion

In this test, fetching 10 posts concurrently was about 6.8 times faster on
average than fetching them one by one (2.18 s against 14.73 s). The time is
spent waiting for the network, and async overlaps those waits. The speed-up is
below 10 times, which is the most that overlapping 10 requests can give, and
that fits this picture. Not all of the gap comes from concurrency, though: the
sync version also pays the cost of setting up a connection on every request
(see the limitations).

## Limitations

- **The sync baseline is not fair.** `requests.get` sets up a new connection on
  every call, while a `requests.Session` reuses connections. Part of the sync
  time is probably connection setup, so these numbers overstate what
  concurrency alone gives. This was **not measured**: the runner has no
  `Session` variant. Adding a third column (sync with `Session`) would separate
  the two effects.
- **One API, one network, one moment.** The workload is 10 requests to one
  public API. The gap would change with more requests, slower or faster
  responses, or a different connection.
- **Fixed order.** In every iteration the async version runs before the sync
  one, so caches or warm connections may favour one side. The order was not
  randomised.
- **Async includes setup.** Each async run creates a new event loop and a new
  HTTP client, and that time is counted.
- **Small sample.** 20 iterations, about 400 requests in total to a free public
  service. Repeating it much more would not be polite.
