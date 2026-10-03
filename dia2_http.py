import requests

r = requests.get("https://jsonplaceholder.typicode.com/posts/1")
print("Código de estado:", r.status_code)
print("Cabeceras:", dict(r.headers))
print("Cuerpo (JSON):", r.json())
