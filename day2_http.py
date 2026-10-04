import requests

r = requests.get("https://jsonplaceholder.typicode.com/posts/1")
print("Status code:", r.status_code)
print("Headers:", dict(r.headers))
print("Body (JSON):", r.json())
