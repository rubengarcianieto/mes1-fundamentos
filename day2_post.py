import requests

nuevo_post = {"title": "orchestation test", "body": "content example", "userId": 1}

r = requests.post("https://jsonplaceholder.typicode.com/posts", json=nuevo_post)
print(r.status_code)  # 201 expected
print(r.json())
