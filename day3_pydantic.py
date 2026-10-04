import requests
from typing import Optional
from pydantic import BaseModel

class Post(BaseModel):
    userId: int
    id: int
    title: str
    body: str

class Comment(BaseModel):
    author: str
    text: str
    approved: bool = False
    grade: Optional[str] = None

r = requests.get("https://jsonplaceholder.typicode.com/posts/1")
data = r.json()
print("Raw dictionary:", data)

post = Post(**data)
print("Validated object:", post)
print("Field access:", post.title)

