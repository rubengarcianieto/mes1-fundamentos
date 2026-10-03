import requests

nuevo_post = {"title": "prueba orquestación", "body": "contenido de ejemplo", "userId": 1}

r = requests.post("https://jsonplaceholder.typicode.com/posts", json=nuevo_post)
print(r.status_code)  # 201 esperado
print(r.json())

