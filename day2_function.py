import requests


def get_post(id: int) -> dict:
    r = requests.get(f"https://jsonplaceholder.typicode.com/posts/{id}")
    if r.status_code == 404:
        raise ValueError(f"There is no post with id {id}")
    r.raise_for_status()
    return r.json()


print(get_post(1))
print(get_post(99999))  # must raise ValueError
