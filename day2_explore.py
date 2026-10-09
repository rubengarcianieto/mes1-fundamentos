import requests

r = requests.get("https://jsonplaceholder.typicode.com/posts/1")

print(type(r))  # qué clase de objeto es
print([name for name in dir(r) if not name.startswith("_")])  # todo lo que contiene
