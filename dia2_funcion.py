import requests

def obtener_post(id: int) -> dict:
    r = requests.get(f"https://jsonplaceholder.typicode.com/posts/{id}")
    if r.status_code == 404:
        raise ValueError(f"No existe ningún post con id {id}")
    r.raise_for_status()
    return r.json()

print(obtener_post(1))
print(obtener_post(99999))  # debe lanzar ValueError
